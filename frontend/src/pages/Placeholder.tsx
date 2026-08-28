import { AppShell } from "../layouts/AppShell";
import { AuthShell } from "../layouts/AuthShell";
import { BlueprintCorners } from "../components/BlueprintCorners";

/**
 * Stand-in body for the routes whose content belongs to a later task. Each route
 * is declared and mounted *now*, inside its real shell, so the shell/routing
 * seam is proven before any page fills it — swapping this component out is the
 * whole change those tasks need to make at the routing layer.
 */
export function Placeholder({
  title,
  task,
  shell,
}: {
  title: string;
  task: string;
  shell: "app" | "auth";
}) {
  const body = (
    <div className="card blueprint" style={{ maxWidth: 420 }}>
      <BlueprintCorners />
      <span className="card-kicker">Not implemented yet</span>
      <span className="card-title">{title}</span>
      <p className="card-body">This screen is built in {task}.</p>
    </div>
  );

  return shell === "auth" ? <AuthShell>{body}</AuthShell> : <AppShell>{body}</AppShell>;
}
