import { useState } from "react";
import { Link, useLocation } from "@tanstack/react-router";
import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
}

const navItems: NavItem[] = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/candidates", icon: Users, label: "Candidates" },
  { to: "/positions", icon: Briefcase, label: "Positions" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "border-r bg-muted/40 transition-all duration-300 flex flex-col",
        collapsed ? "w-16" : "w-60"
      )}
    >
      <div className="flex-1 p-2 pt-4">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to;

            return (
              <Link key={item.to} to={item.to}>
                {({ isActive: linkActive }) => (
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start transition-colors",
                      collapsed ? "px-2" : "px-3",
                      (isActive || linkActive) &&
                        "bg-accent text-accent-foreground"
                    )}
                  >
                    <Icon className={cn("h-5 w-5", !collapsed && "mr-3")} />
                    {!collapsed && <span>{item.label}</span>}
                  </Button>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <Separator />

      <div className="p-2">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-center"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
