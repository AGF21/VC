import { ConnectionForm } from '@/components/ServerSettings/ConnectionForm';
import { ServerStatus } from '@/components/ServerSettings/ServerStatus';
import { UpdateStatus } from '@/components/ServerSettings/UpdateStatus';
import { usePlatform } from '@/platform/PlatformContext';

export function ServerTab() {
  const platform = usePlatform();
  return (
    <div className="space-y-4 overflow-y-auto flex flex-col">
      <div className="grid gap-4 md:grid-cols-2">
        <ConnectionForm />
        <ServerStatus />
      </div>
      {platform.metadata.isTauri && <UpdateStatus />}
      <div className="py-8 text-center">
        <span style={{ fontFamily: 'Impact, Haettenschweiler, "Arial Narrow Bold", sans-serif', color: 'white', fontSize: '1.25rem', letterSpacing: '0.05em' }}>Zest Tech</span>
      </div>
    </div>
  );
}
