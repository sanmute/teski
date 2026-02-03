import { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";

type Props = { children: ReactNode };
type State = { hasError: boolean; message?: string };

export class AppErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error("[AppErrorBoundary]", error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
          <div>
            <h1 className="text-2xl font-semibold">Something went off-track</h1>
            <p className="text-sm text-muted-foreground">
              The demo kept running, but this view hit an error. Try reloading to continue exploring.
            </p>
            {this.state.message && (
              <p className="mt-2 text-xs text-muted-foreground">Details: {this.state.message}</p>
            )}
          </div>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
