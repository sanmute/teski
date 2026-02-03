import { PropsWithChildren } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  CalendarDays,
  HelpCircle,
  LayoutDashboard,
  ListCheck,
  NotebookPen,
  Plus,
  RotateCcw,
  Timer,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { DEMO_MODE } from "@/config/demo";

const navItems = [
  { label: "Today", to: "/today", icon: CalendarDays },
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Tasks", to: "/tasks/upcoming", icon: ListCheck },
  { label: "Study", to: "/study", icon: Timer },
  { label: "Exercises", to: "/exercises", icon: NotebookPen },
  { label: "Reviews", to: "/reviews", icon: RotateCcw },
  { label: "My Stats", to: "/stats", icon: BarChart3 },
  { label: "Help", to: "/help", icon: HelpCircle },
  { label: "Profile", to: "/profile", icon: User },
];

const TITLE_MAP: Record<string, string> = {
  "/today": "Today",
  "/": "Dashboard",
  "/tasks/upcoming": "Upcoming tasks",
  "/study": "Study",
  "/exercises": "Exercises",
  "/help": "Help & explanations",
  "/reviews": "Reviews",
  "/stats": "My stats",
  "/profile": "My study profile",
};

export function AppLayout({ children }: PropsWithChildren) {
  const location = useLocation();
  const navigate = useNavigate();
  const pathname = location.pathname;
  const title =
    pathname.startsWith("/study/session")
      ? "Study session"
      : TITLE_MAP[pathname] ?? "Teski";

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="hidden md:flex w-60 flex-col border-r bg-card">
        <div className="px-4 py-5">
          <div className="text-lg font-semibold">Teski</div>
          <p className="text-xs text-muted-foreground">Personalized study companion</p>
        </div>
        <nav className="mt-4 flex-1 space-y-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition hover:bg-muted",
                    isActive && "bg-muted text-primary"
                  )
                }
              >
                {Icon && <Icon className="h-4 w-4" />}
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b px-4 py-3">
          <div>
            <h1 className="text-xl font-semibold">{title}</h1>
            <p className="text-xs text-muted-foreground">Teski adapts plans to your style.</p>
          </div>
          <Button size="sm" onClick={() => navigate("/tasks/upcoming")}>
            <Plus className="mr-1 h-4 w-4" />
            New task
          </Button>
        </header>
        <main className="flex-1 px-4 py-4">
          {children ?? <Outlet />}
        </main>
        {DEMO_MODE && (
          <footer className="border-t px-4 py-2 text-center text-[11px] text-muted-foreground">
            Demo mode — illustrative data
          </footer>
        )}
      </div>
    </div>
  );
}
