import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import AdminCostPanel from "./pages/AdminCostPanel";
import PilotSignup from "./pages/PilotSignup";
import PilotAdmin from "./pages/PilotAdmin";
import InvestorDashboard from "./pages/InvestorDashboard";
import DeepLearningLab from "./pages/DeepLearningLab";
import { useEffect, useState } from "react";
import { PetFrog, CompanionCharacter } from "@/components/PetFrog";
import { FeedbackButton } from "@/components/FeedbackButton";
// >>> PERSONA START
import PersonaPreviewPage from "./pages/PersonaPreview";
// <<< PERSONA END
import TasksUpcoming from "./pages/TasksUpcoming";
import Dashboard from "./pages/Dashboard";
import Study from "./pages/Study";
import Help from "./pages/Help";
import Profile from "./pages/Profile";
import { AppLayout } from "./layouts/AppLayout";
import StudySessionPage from "./pages/StudySessionPage";

const queryClient = new QueryClient();

const App = () => {
  const [companion, setCompanion] = useState<CompanionCharacter>(() => {
    if (typeof window === "undefined") return "frog";
    const stored = window.localStorage.getItem("assistant-character");
    return stored === "cat" ? "cat" : stored === "frog" ? "frog" : "frog";
  });

  const [showCharacterModal, setShowCharacterModal] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return !window.localStorage.getItem("assistant-character");
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("assistant-character", companion);
      setShowCharacterModal(false);
    }
  }, [companion]);

  const [frogState, setFrogState] = useState<{
    isVisible: boolean;
    urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done';
    message: string;
  }>({
    isVisible: false,
    urgency: 'calm',
    message: ''
  });
  const currentUserId: string | undefined = undefined;

  const handleTriggerFrog = (urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done', message: string) => {
    setFrogState({
      isVisible: true,
      urgency,
      message
    });
  };

  const handleDismissFrog = () => {
    setFrogState(prev => ({ ...prev, isVisible: false }));
  };

  // >>> PERSONA START
  const personaRoutes = (
    <Route path="/personas/preview" element={<PersonaPreviewPage />} />
  );
  // <<< PERSONA END

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        themes={["light", "dark"]}
        storageKey="teski-theme"
        enableSystem={false}
      >
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/tasks/upcoming" element={<TasksUpcoming />} />
                <Route path="/study" element={<Study />} />
                <Route path="/study/session/:sessionId" element={<StudySessionPage />} />
                <Route path="/help" element={<Help />} />
                <Route path="/profile" element={<Profile />} />
              </Route>
              <Route
                path="/legacy"
                element={
                  <Index
                    onTriggerFrog={handleTriggerFrog}
                    companion={companion}
                    onCompanionChange={setCompanion}
                  />
                }
              />
              <Route path="/admin/costs" element={<AdminCostPanel />} />
              <Route path="/admin/investor" element={<InvestorDashboard />} />
              <Route path="/pilot/signup" element={<PilotSignup />} />
              <Route path="/pilot/admin" element={<PilotAdmin />} />
              <Route path="/deep" element={<DeepLearningLab />} />
              {personaRoutes}
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
          
          {/* Global Pet Frog */}
          <PetFrog
            character={companion}
            urgency={frogState.urgency}
            message={frogState.message}
            isVisible={frogState.isVisible}
            onDismiss={handleDismissFrog}
          />

          <FeedbackButton userId={currentUserId} />

          {showCharacterModal && (
            <CharacterChooser
              current={companion}
              onSelect={(choice) => setCompanion(choice)}
            />
          )}
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

interface CharacterChooserProps {
  current: CompanionCharacter;
  onSelect: (character: CompanionCharacter) => void;
}

const CharacterChooser = ({ current, onSelect }: CharacterChooserProps) => {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-background/80 backdrop-blur">
      <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-8 shadow-2xl">
        <h2 className="text-2xl font-semibold text-center mb-2">Who’s keeping you accountable?</h2>
        <p className="text-sm text-muted-foreground text-center mb-6">
          Pick your motivational companion. You can change this later in Settings.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => onSelect('frog')}
            className={
              `rounded-xl border p-4 transition hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary/60 ${
                current === 'frog' ? 'border-primary bg-primary/10' : 'border-border bg-muted/40'
              }`
            }
          >
            <div className="flex flex-col items-center gap-3">
              <img src="/teski-frog.svg" alt="Teski the Frog" className="h-20 w-20" />
              <div className="text-lg font-semibold">Teski the Frog</div>
              <p className="text-xs text-muted-foreground text-center">
                Energetic croaks, playful nudges, and guilt-trips with a smile.
              </p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => onSelect('cat')}
            className={
              `rounded-xl border p-4 transition hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary/60 ${
                current === 'cat' ? 'border-primary bg-primary/10' : 'border-border bg-muted/40'
              }`
            }
          >
            <div className="flex flex-col items-center gap-3">
              <img src="/duey-cat.svg" alt="Duey the Cat" className="h-20 w-20" />
              <div className="text-lg font-semibold">Duey the Cat</div>
              <p className="text-xs text-muted-foreground text-center">
                Cool-headed reminders with a hint of smug satisfaction when you succeed.
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
