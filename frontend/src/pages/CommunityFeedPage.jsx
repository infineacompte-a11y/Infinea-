import React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Search, Users, Trophy, ChevronRight, Activity } from "lucide-react";
import Sidebar from "@/components/Sidebar";

/**
 * CommunityFeedPage — Community hub (activity feed placeholder).
 * Sprint 2 will add the full activity feed here.
 * For now, serves as a navigation hub to social features.
 *
 * Route: /community
 */
export default function CommunityFeedPage() {
  const links = [
    {
      to: "/search",
      icon: Search,
      title: "Rechercher des membres",
      desc: "Trouvez et suivez d'autres utilisateurs",
      color: "#459492",
    },
    {
      to: "/groups",
      icon: Users,
      title: "Mes groupes",
      desc: "Progressez ensemble avec vos proches",
      color: "#459492",
    },
    {
      to: "/challenges",
      icon: Trophy,
      title: "Défis communautaires",
      desc: "Participez aux défis et grimpez le classement",
      color: "#E48C75",
    },
  ];

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Communauté
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Connectez-vous avec les autres membres
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Coming soon banner */}
            <Card className="mb-6 border-dashed border-[#459492]/30 bg-gradient-to-br from-[#459492]/5 to-transparent opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5 flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-[#459492]/10 flex items-center justify-center shrink-0">
                  <Activity className="w-5 h-5 text-[#459492]" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Le fil d'activité arrive bientôt
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Suivez la progression de vos amis en temps réel.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Quick links */}
            <div className="space-y-3">
              {links.map((link, index) => (
                <Link key={link.to} to={link.to}>
                  <Card
                    className="hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer opacity-0 animate-fade-in"
                    style={{
                      animationDelay: `${200 + index * 80}ms`,
                      animationFillMode: "forwards",
                    }}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                        style={{ backgroundColor: `${link.color}15` }}
                      >
                        <link.icon className="w-6 h-6" style={{ color: link.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-sans font-semibold tracking-tight text-sm">
                          {link.title}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {link.desc}
                        </p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
