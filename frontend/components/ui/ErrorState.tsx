import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";

interface ErrorStateProps { message?: string; onRetry?: () => void; }

const FRIENDLY: Record<string, string> = {
  "upload":  "We had trouble reading that file. Try a clearer photo or a different format.",
  "timeout": "This is taking longer than usual. We're still working on it.",
  "partial": "We found most of your letter's details. Please confirm a few things below.",
};

export function ErrorState({ message = "timeout", onRetry }: ErrorStateProps) {
  const display = FRIENDLY[message] ?? message;
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center">
        <AlertTriangle className="text-amber-400" size={22} />
      </div>
      <p className="text-slate-300 max-w-sm">{display}</p>
      {onRetry && <Button variant="secondary" size="sm" onClick={onRetry}>Try again</Button>}
    </div>
  );
}
