import React, { useState, useCallback, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Search, Users, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import UserCard from "@/components/UserCard";

/**
 * SearchPage — Discover and search users.
 * Pattern: Instagram search + Strava athlete finder.
 *
 * Route: /search
 */
export default function SearchPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const debounceRef = useRef(null);

  const doSearch = useCallback(async (q) => {
    if (q.length < 2) {
      setResults([]);
      setHasSearched(false);
      return;
    }

    setIsSearching(true);
    try {
      const res = await authFetch(
        `${API}/users/search?q=${encodeURIComponent(q)}&limit=20`
      );
      if (!res.ok) throw new Error("Erreur");
      const data = await res.json();
      setResults(data.users || []);
      setHasSearched(true);
    } catch {
      toast.error("Erreur lors de la recherche");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val.trim()), 350);
  };

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Rechercher
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Trouvez des utilisateurs et suivez leur progression
            </p>

            {/* Search input */}
            <div className="relative mt-5 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                type="text"
                value={query}
                onChange={handleInputChange}
                placeholder="Nom ou @identifiant..."
                autoComplete="off"
                autoFocus
                className="pl-10 h-12 rounded-xl bg-[#1a3a3d] border-white/15 text-white placeholder:text-white/40 focus:bg-[#1f4447] focus:border-white/30 caret-white transition-all"
              />
              {isSearching && (
                <Loader2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 animate-spin" />
              )}
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Results */}
            {hasSearched && results.length === 0 && !isSearching && (
              <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <Users className="w-7 h-7 text-primary" />
                </div>
                <h2 className="text-base font-semibold text-foreground mb-1">
                  Aucun résultat
                </h2>
                <p className="text-muted-foreground text-sm max-w-xs">
                  Essayez un autre nom ou vérifiez l'orthographe.
                </p>
              </div>
            )}

            {!hasSearched && !isSearching && (
              <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <Search className="w-7 h-7 text-primary" />
                </div>
                <h2 className="text-base font-semibold text-foreground mb-1">
                  Découvrez la communauté
                </h2>
                <p className="text-muted-foreground text-sm max-w-xs">
                  Tapez au moins 2 caractères pour rechercher des utilisateurs.
                </p>
              </div>
            )}

            {results.length > 0 && (
              <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <p className="text-xs text-muted-foreground mb-3">
                  {results.length} résultat{results.length > 1 ? "s" : ""}
                </p>
                {results.map((u, index) => (
                  <div
                    key={u.user_id}
                    className="opacity-0 animate-fade-in"
                    style={{
                      animationDelay: `${index * 50}ms`,
                      animationFillMode: "forwards",
                    }}
                  >
                    <UserCard
                      user={{
                        user_id: u.user_id,
                        name: u.display_name,
                        username: u.username,
                        picture: u.avatar_url,
                        is_following: u.is_following || false,
                      }}
                      currentUserId={user?.user_id}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
