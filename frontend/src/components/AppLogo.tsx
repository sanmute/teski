import { CheckSquare2 } from "lucide-react";

export function AppLogo() {
  return (
    <div className="inline-flex flex-col items-center text-center select-none">
      <div className="flex items-end gap-3 text-5xl font-black tracking-tight text-emerald-700">
        <span className="relative pl-8 leading-none">
          Teski
          <img
            src="/teski-frog.png"
            alt="Teski mascot"
            className="absolute -top-12 left-0 w-16 drop-shadow-[0_10px_14px_rgba(16,24,16,0.35)]"
          />
        </span>
        <CheckSquare2 className="h-10 w-10 text-emerald-500" aria-hidden />
      </div>
    </div>
  );
}
