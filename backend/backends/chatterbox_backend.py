"""
Chatterbox TTS backend implementation for fast 350M model with emotion/sound tags.
"""

from typing import Optional, List, Tuple
import asyncio
import torch
import numpy as np
from pathlib import Path

from . import TTSBackend
from ..utils.cache import get_cache_key, get_cached_voice_prompt, cache_voice_prompt
from ..utils.audio import normalize_audio, load_audio
from ..utils.progress import get_progress_manager
from ..utils.tasks import get_task_manager


class ChatterboxTTSBackend:
    """Chatterbox TTS backend using chatterbox-tts library."""

    def __init__(self):
        self.model = None
        self.model_type = "chatterbox"
        self.device = self._get_device()
        self._is_loaded = False

    def _get_device(self) -> str:
        """Get the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "cpu"
        return "cpu"

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded and self.model is not None

    def _get_model_path(self, model_size: str = "turbo") -> str:
        """
        Get the model identifier.

        Args:
            model_size: Model size (only "turbo" is supported)

        Returns:
            Model identifier
        """
        if model_size != "turbo":
            raise ValueError(f"Chatterbox only supports 'turbo' model size, got: {model_size}")
        return "turbo"

    def _is_model_cached(self, model_size: str = "turbo") -> bool:
        """
        Check if the model is cached locally.

        Args:
            model_size: Model size to check

        Returns:
            True if model is cached, False otherwise
        """
        try:
            # Chatterbox caches models in HF cache directory
            from huggingface_hub import constants as hf_constants
            cache_dir = Path(hf_constants.HF_HUB_CACHE)

            # Chatterbox typically caches in resemble-ai/chatterbox-tts
            repo_id = "resemble-ai/chatterbox-tts"
            repo_cache = cache_dir / ("models--" + repo_id.replace("/", "--"))

            if not repo_cache.exists():
                return False

            # Check for .incomplete files
            blobs_dir = repo_cache / "blobs"
            if blobs_dir.exists() and any(blobs_dir.glob("*.incomplete")):
                return False

            # Check for model weight files
            snapshots_dir = repo_cache / "snapshots"
            if snapshots_dir.exists():
                has_weights = (
                    any(snapshots_dir.rglob("*.safetensors")) or
                    any(snapshots_dir.rglob("*.bin")) or
                    any(snapshots_dir.rglob("*.pt"))
                )
                if not has_weights:
                    return False

            return True
        except Exception as e:
            print(f"[_is_model_cached] Error checking cache: {e}")
            return False

    async def load_model_async(self, model_size: str = "turbo"):
        """
        Load the Chatterbox TTS model.

        Args:
            model_size: Model size (only "turbo" supported)
        """
        if self.is_loaded():
            return

        await asyncio.to_thread(self._load_model_sync, model_size)

    load_model = load_model_async

    def _load_model_sync(self, model_size: str = "turbo"):
        """Synchronous model loading."""
        try:
            progress_manager = get_progress_manager()
            task_manager = get_task_manager()
            model_name = "chatterbox-turbo"

            # Check if model is cached
            is_cached = self._is_model_cached(model_size)

            if not is_cached:
                task_manager.start_download(model_name)
                progress_manager.update_progress(
                    model_name=model_name,
                    current=0,
                    total=0,
                    filename="Connecting to HuggingFace...",
                    status="downloading",
                )

            print(f"Loading Chatterbox TTS model on {self.device}...")

            try:
                from chatterbox.tts_turbo import ChatterboxTurboTTS
            except ImportError as e:
                print(f"Error: chatterbox-tts package not found. Install with: pip install chatterbox-tts")
                progress_manager.mark_error(model_name, str(e))
                task_manager.error_download(model_name, str(e))
                raise

            # Load the model
            self.model = ChatterboxTurboTTS.from_pretrained(device=self.device)
            self._is_loaded = True

            if not is_cached:
                progress_manager.mark_complete(model_name)
                task_manager.complete_download(model_name)

            print(f"Chatterbox TTS model loaded successfully")

        except Exception as e:
            print(f"Error loading Chatterbox TTS model: {e}")
            progress_manager = get_progress_manager()
            task_manager = get_task_manager()
            model_name = "chatterbox-turbo"
            progress_manager.mark_error(model_name, str(e))
            task_manager.error_download(model_name, str(e))
            raise

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self._is_loaded = False

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            print("Chatterbox TTS model unloaded")

    async def create_voice_prompt(
        self,
        audio_path: str,
        reference_text: str,
        use_cache: bool = True,
    ) -> Tuple[dict, bool]:
        """
        Create voice prompt from reference audio.

        Args:
            audio_path: Path to reference audio file
            reference_text: Transcript of reference audio
            use_cache: Whether to use cached prompt if available

        Returns:
            Tuple of (voice_prompt_dict, was_cached)
        """
        await self.load_model_async()

        # Check cache if enabled
        if use_cache:
            cache_key = get_cache_key(audio_path, reference_text)
            cached_prompt = get_cached_voice_prompt(cache_key)
            if cached_prompt is not None:
                if isinstance(cached_prompt, dict):
                    return cached_prompt, True

        def _create_prompt_sync():
            """Create voice prompt from reference audio."""
            # For Chatterbox, we store the audio path as the voice prompt
            # Chatterbox uses the audio directly during generation
            return {
                "audio_path": str(audio_path),
                "reference_text": reference_text,
            }

        voice_prompt = await asyncio.to_thread(_create_prompt_sync)

        if use_cache:
            cache_key = get_cache_key(audio_path, reference_text)
            cache_voice_prompt(cache_key, voice_prompt)

        return voice_prompt, False

    async def combine_voice_prompts(
        self,
        audio_paths: List[str],
        reference_texts: List[str],
    ) -> Tuple[np.ndarray, str]:
        """
        Combine multiple reference samples.

        Args:
            audio_paths: List of audio file paths
            reference_texts: List of reference texts

        Returns:
            Tuple of (combined_audio, combined_text)
        """
        combined_audio = []

        for audio_path in audio_paths:
            audio, sr = load_audio(audio_path)
            audio = normalize_audio(audio)
            combined_audio.append(audio)

        mixed = np.concatenate(combined_audio)
        mixed = normalize_audio(mixed)
        combined_text = " ".join(reference_texts)

        return mixed, combined_text

    async def generate(
        self,
        text: str,
        voice_prompt: dict,
        language: str = "en",
        seed: Optional[int] = None,
        instruct: Optional[str] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Generate audio from text using voice prompt.

        Chatterbox supports paralinguistic tags like [cough], [laugh], [chuckle]
        and emotion/sound tags can be included in the text.

        Args:
            text: Text to synthesize (can include [emotion/sound] tags)
            voice_prompt: Voice prompt dict with audio_path and reference_text
            language: Language code (only 'en' supported)
            seed: Random seed (not used by Chatterbox)
            instruct: Instruction text (can include emotion/sound tags)

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        await self.load_model_async()

        # If instruct is provided, append it to the text for emotion/sound tags
        full_text = text
        if instruct:
            full_text = f"{text} {instruct}"

        def _generate_sync():
            """Generate audio using Chatterbox."""
            audio_prompt_path = voice_prompt.get("audio_path")

            # Generate audio with voice cloning
            # Chatterbox returns audio at 23+ kHz sample rate
            audio_data = self.model(
                text=full_text,
                audio_prompt_path=audio_prompt_path,
            )

            # Convert to numpy array if needed
            if isinstance(audio_data, torch.Tensor):
                audio = audio_data.detach().cpu().float().numpy()
            elif isinstance(audio_data, tuple):
                # Some versions return (audio, sr)
                audio, sr = audio_data
                if isinstance(audio, torch.Tensor):
                    audio = audio.detach().cpu().float().numpy()
                return np.asarray(audio, dtype=np.float32), int(sr)
            else:
                audio = np.asarray(audio_data, dtype=np.float32)

            # Chatterbox operates at 23+ kHz (typically 23500 Hz or similar)
            # Estimate sample rate based on expected audio duration
            # For now, assume 23500 Hz as default
            sample_rate = 23500

            return audio, sample_rate

        audio, sample_rate = await asyncio.to_thread(_generate_sync)

        return audio, sample_rate
