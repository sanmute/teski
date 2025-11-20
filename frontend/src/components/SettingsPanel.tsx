import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings, Sun, Moon, Trash2, Frown, Eye, Type, Palette, LayoutGrid } from "lucide-react";
import { useTheme } from "next-themes";
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { CompanionCharacter } from "@/components/PetFrog";
import { DeepPrefs } from "@/components/DeepPrefs";
import { DEMO_USER_ID } from "@/lib/constants";
import { getPersonaProfile, updatePersonaProfile, type PersonaProfile } from "@/api";

interface SettingsPanelProps {
  demoMode: boolean;
  onDemoModeChange: (enabled: boolean) => void;
  companion: CompanionCharacter;
  onCompanionChange: (character: CompanionCharacter) => void;
  userId?: string;
}

export function SettingsPanel({ demoMode, onDemoModeChange, companion, onCompanionChange, userId }: SettingsPanelProps) {
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const resolvedUserId = userId ?? DEMO_USER_ID;
  const isDemoUser = resolvedUserId === DEMO_USER_ID;
  const personaDescriptions: Record<string, string> = {
    calm: "Gentle encouragement and steady pacing.",
    snark: "Playful jabs that keep you accountable without cruelty.",
    hype: "High-energy coach cheering for every rep.",
    professor: "Analytical, precise, and focused on rigor.",
  };

  const readLocalStorage = <T,>(key: string, fallback: T, transform?: (raw: string) => T): T => {
    if (typeof window === 'undefined') return fallback;
    const raw = window.localStorage.getItem(key);
    if (raw == null) return fallback;
    try {
      return transform ? transform(raw) : ((raw as unknown) as T);
    } catch {
      return fallback;
    }
  };

  // Settings state with localStorage persistence
  const [frogIntensity, setFrogIntensity] = useState<number>(() =>
    readLocalStorage('frog-intensity', 5, (raw) => parseInt(raw, 10) || 5)
  );

  const [defaultTaskView, setDefaultTaskView] = useState<string>(() =>
    readLocalStorage('default-task-view', 'all')
  );

  const [archiveCompleted, setArchiveCompleted] = useState<boolean>(() =>
    readLocalStorage('archive-completed', false, (raw) => raw === 'true')
  );

  const [fontSize, setFontSize] = useState<number>(() =>
    readLocalStorage('font-size', 2, (raw) => parseInt(raw, 10) || 2)
  );

  const [highContrast, setHighContrast] = useState<boolean>(() =>
    readLocalStorage('high-contrast', false, (raw) => raw === 'true')
  );

  const [reducedMotion, setReducedMotion] = useState<boolean>(() =>
    readLocalStorage('reduced-motion', false, (raw) => raw === 'true')
  );

  const [colorBlindSupport, setColorBlindSupport] = useState<string>(() =>
    readLocalStorage('color-blind-support', 'default')
  );
  const [personaProfile, setPersonaProfile] = useState<PersonaProfile | null>(null);
  const [personaLoading, setPersonaLoading] = useState(false);
  const [personaError, setPersonaError] = useState<string | null>(null);

  // Save to localStorage on changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('frog-intensity', frogIntensity.toString());
  }, [frogIntensity]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('default-task-view', defaultTaskView);
  }, [defaultTaskView]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('archive-completed', archiveCompleted.toString());
  }, [archiveCompleted]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('font-size', fontSize.toString());
  }, [fontSize]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('high-contrast', highContrast.toString());
  }, [highContrast]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('reduced-motion', reducedMotion.toString());
  }, [reducedMotion]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('color-blind-support', colorBlindSupport);
  }, [colorBlindSupport]);

  useEffect(() => {
    if (!resolvedUserId || isDemoUser) return;
    setPersonaLoading(true);
    getPersonaProfile(resolvedUserId)
      .then((profile) => {
        setPersonaProfile(profile);
        setPersonaError(null);
      })
      .catch((err) => {
        console.error(err);
        setPersonaError("Could not load persona.");
      })
      .finally(() => setPersonaLoading(false));
  }, [resolvedUserId, isDemoUser]);

  const applyAppearance = useCallback(() => {
    const body = document.body;
    const root = document.getElementById("root");

    body.classList.remove(
      "font-size-small",
      "font-size-normal",
      "font-size-large",
      "font-size-extra-large",
      "high-contrast",
      "reduced-motion",
    );
    if (root) {
      root.classList.remove("color-blind-deuteranopia", "color-blind-protanopia", "color-blind-tritanopia");
    }

    const fontSizeClasses = ["font-size-small", "font-size-normal", "font-size-large", "font-size-extra-large"];
    body.classList.add(fontSizeClasses[fontSize - 1]);

    if (highContrast) {
      body.classList.add("high-contrast");
    }
    if (reducedMotion) {
      body.classList.add("reduced-motion");
    }
    if (colorBlindSupport !== "default" && root) {
      root.classList.add(`color-blind-${colorBlindSupport}`);
    }
  }, [fontSize, highContrast, reducedMotion, colorBlindSupport]);

  const applySettings = () => {
    applyAppearance();
    toast({
      title: "Settings applied successfully",
      description: "Your appearance preferences have been updated.",
    });
  };

  const handlePersonaChange = async (value: string) => {
    if (!resolvedUserId || isDemoUser) return;
    try {
      setPersonaLoading(true);
      const profile = await updatePersonaProfile({ user_id: resolvedUserId, persona: value });
      setPersonaProfile(profile);
      setPersonaError(null);
      toast({
        title: "Persona updated",
        description: `${value.charAt(0).toUpperCase()}${value.slice(1)} persona activated.`,
      });
    } catch (err) {
      console.error(err);
      setPersonaError("Could not update persona.");
      toast({
        title: "Could not update persona",
        description: "Please try again.",
        variant: "destructive",
      });
    } finally {
      setPersonaLoading(false);
    }
  };

  // Apply saved settings on component mount
  useEffect(() => {
    applyAppearance();
  }, [applyAppearance]);

  const handleDeleteAllData = () => {
    // Backend logic will be handled separately
    toast({
      title: "Data deletion requested",
      description: "All user data will be cleared from the system.",
      variant: "destructive"
    });
  };

  const getFontSizeLabel = (value: number) => {
    const labels = ['Small', 'Normal', 'Large', 'Extra Large'];
    return labels[value - 1] || 'Normal';
  };

  const getIntensityLabel = (value: number) => {
    if (value <= 3) return 'Mild Sassiness';
    if (value <= 6) return 'Balanced Sarcasm Approach';
    return 'Maximum Sarcasm and Sternness';
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        
        <Tabs defaultValue="frog" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="frog" className="flex items-center gap-1">
              <Frown className="h-3 w-3" />
              Companion
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center gap-1">
              <LayoutGrid className="h-3 w-3" />
              Tasks
            </TabsTrigger>
            <TabsTrigger value="accessibility" className="flex items-center gap-1">
              <Eye className="h-3 w-3" />
              Access
            </TabsTrigger>
            <TabsTrigger value="display" className="flex items-center gap-1">
              <Palette className="h-3 w-3" />
              Display
            </TabsTrigger>
            <TabsTrigger value="danger" className="flex items-center gap-1">
              <Trash2 className="h-3 w-3" />
              User data
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-4 overflow-y-auto max-h-[60vh]">
            <TabsContent value="frog" className="space-y-4 mt-0">
              <div className="space-y-4">
                <div className="space-y-3 rounded-xl border border-border bg-muted/30 p-4">
                  <div className="flex items-center justify-between">
                    <Label>Persona reaction voice</Label>
                    {personaLoading && <span className="text-xs text-muted-foreground">Updating…</span>}
                  </div>
                  <Select
                    value={personaProfile?.persona ?? "calm"}
                    onValueChange={handlePersonaChange}
                    disabled={personaLoading || isDemoUser}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a persona" />
                    </SelectTrigger>
                    <SelectContent>
                      {(personaProfile?.available_personas ?? ["calm", "snark", "hype", "professor"]).map((option) => (
                        <SelectItem key={option} value={option}>
                          {option.charAt(0).toUpperCase() + option.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {personaError && <p className="text-xs text-destructive">{personaError}</p>}
                  {isDemoUser ? (
                    <p className="text-xs text-muted-foreground">Sign in to change personas.</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      {personaDescriptions[personaProfile?.persona ?? "calm"]}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Companion Sass Level: {getIntensityLabel(frogIntensity)}</Label>
                  <Slider
                    value={[frogIntensity]}
                    onValueChange={(value) => setFrogIntensity(value[0])}
                    max={10}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                  <div className="text-xs text-muted-foreground">
                    Slide to adjust how harsh or gentle the frog's personality is
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Mood translator</Label>
                  <div className="text-sm text-muted-foreground space-y-1 p-3 bg-muted/50 rounded-md">
                    <div><strong>1-3: 😌 Gentle nudges</strong></div>
                    <div><strong>4-6: 😤 Stern reminders</strong></div>  
                    <div><strong>7-10: 🤬 Full accountability fury</strong></div>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label>Choose your accountability companion</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => onCompanionChange('frog')}
                      className={cn(
                        'rounded-lg border p-3 transition hover:shadow focus:outline-none focus:ring-2 focus:ring-primary/60',
                        companion === 'frog' ? 'border-primary bg-primary/10' : 'border-border bg-muted/40'
                      )}
                    >
                      <div className="flex flex-col items-center gap-2">
                        <img src="/teski-frog.svg" alt="Teski the Frog" className="h-16 w-16" />
                        <div className="text-sm font-semibold">Teski the Frog</div>
                        <p className="text-xs text-muted-foreground text-center">
                          Pep talks with a playful croak and just enough sass.
                        </p>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => onCompanionChange('cat')}
                      className={cn(
                        'rounded-lg border p-3 transition hover:shadow focus:outline-none focus:ring-2 focus:ring-primary/60',
                        companion === 'cat' ? 'border-primary bg-primary/10' : 'border-border bg-muted/40'
                      )}
                    >
                      <div className="flex flex-col items-center gap-2">
                        <img src="/duey-cat.svg" alt="Duey the Cat" className="h-16 w-16" />
                        <div className="text-sm font-semibold">Duey the Cat</div>
                        <p className="text-xs text-muted-foreground text-center">
                          Cool-headed reports with a side of smug approval.
                        </p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="tasks" className="space-y-4 mt-0">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="task-view">Default Task View</Label>
                  <Select value={defaultTaskView} onValueChange={setDefaultTaskView}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All tasks</SelectItem>
                      <SelectItem value="next-7-days">Next 7 days only</SelectItem>
                      <SelectItem value="overdue">Overdue tasks only</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-xs text-muted-foreground">
                    Choose which tasks to display by default
                  </div>
                </div>
                
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label>Archive Completed Tasks</Label>
                    <div className="text-xs text-muted-foreground">
                      Auto-hide completed tasks after 48 hours
                    </div>
                  </div>
                  <Switch
                    checked={archiveCompleted}
                    onCheckedChange={setArchiveCompleted}
                  />
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="accessibility" className="space-y-4 mt-0">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Font Size: {getFontSizeLabel(fontSize)}</Label>
                  <Slider
                    value={[fontSize]}
                    onValueChange={(value) => setFontSize(value[0])}
                    max={4}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                  <div className="text-xs text-muted-foreground">
                    Adjust text size for better readability
                  </div>
                </div>
                
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label>High Contrast Mode</Label>
                    <div className="text-xs text-muted-foreground">
                      Enhanced visibility option
                    </div>
                  </div>
                  <Switch
                    checked={highContrast}
                    onCheckedChange={setHighContrast}
                  />
                </div>
                
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label>Reduced Motion</Label>
                    <div className="text-xs text-muted-foreground">
                      Disable animations for accessibility
                    </div>
                  </div>
                  <Switch
                    checked={reducedMotion}
                    onCheckedChange={setReducedMotion}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="color-blind">Color Blind Support</Label>
                  <Select value={colorBlindSupport} onValueChange={setColorBlindSupport}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Default</SelectItem>
                      <SelectItem value="deuteranopia">Deuteranopia (red-green)</SelectItem>
                      <SelectItem value="protanopia">Protanopia (red-green)</SelectItem>
                      <SelectItem value="tritanopia">Tritanopia (blue-yellow)</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-xs text-muted-foreground">
                    Alternative color schemes for color blindness
                  </div>
                </div>
                
                <div className="pt-4 border-t">
                  <Button 
                    onClick={applySettings}
                    size="sm"
                    variant="outline"
                    className="ml-auto"
                  >
                    <Type className="h-3 w-3 mr-1" />
                    Apply Changes
                  </Button>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="display" className="space-y-4 mt-0">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Theme</Label>
                  <div className="flex gap-2">
                    <Button
                      variant={theme === "light" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("light")}
                      className="flex items-center gap-2"
                    >
                      <Sun className="h-4 w-4" />
                      Light
                    </Button>
                    <Button
                      variant={theme === "dark" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTheme("dark")}
                      className="flex items-center gap-2"
                    >
                      <Moon className="h-4 w-4" />
                      Dark
                    </Button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Choose your preferred color theme
                  </div>
                </div>
                
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label>Demo Mode</Label>
                    <div className="text-xs text-muted-foreground">
                      Show sample tasks for demonstration
                    </div>
                  </div>
                  <Switch
                    checked={demoMode}
                    onCheckedChange={onDemoModeChange}
                  />
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="danger" className="space-y-4 mt-0">
              <div className="space-y-4">
                <div className="p-4 border border-destructive/20 rounded-lg bg-destructive/5">
                  <Label className="text-destructive text-base">⚠️ Danger Zone</Label>
                  <p className="text-sm text-muted-foreground mt-2 mb-4">
                    These actions are irreversible and will permanently affect your data.
                  </p>
                  
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button 
                        variant="destructive" 
                        size="sm" 
                        className="w-full flex items-center gap-2"
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete All User Data
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete All User Data</AlertDialogTitle>
                        <AlertDialogDescription>
                          This action cannot be undone. This will permanently delete all your 
                          stored assignments, preferences, and account data from our servers.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                          onClick={handleDeleteAllData}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Yes, delete everything
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </TabsContent>
          </div>
          <div className="mt-6">
            <DeepPrefs userId={resolvedUserId} />
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
