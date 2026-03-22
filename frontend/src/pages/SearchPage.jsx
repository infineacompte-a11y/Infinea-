import React, { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Search, Loader2, Users } from "lucide-react";
import api from "@/lib/api";
import AppLayout from "@/components/AppLayout";
import UserCard from "@/components/UserCard";
import { toast } from "sonner";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [followStates, setFollowStates] = useState({});
  const debounceRef = useRef(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await api.searchUsers(query);
        setResults(data.users);
        setSearched(true);
      } catch (err) {
        if (err.status !== 400) toast.error(err.message);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  const handleFollow = async (userId) => {
    setFollowStates((s) => ({ ...s, [userId]: "loading" }));
    try {
      await api.follow(userId);
      setFollowStates((s) => ({ ...s, [userId]: "following" }));
      toast.success("Vous suivez cet utilisateur");
    } catch (err) {
      setFollowStates((s) => ({ ...s, [userId]: undefined }));
      toast.error(err.message);
    }
  };

  const handleUnfollow = async (userId) => {
    setFollowStates((s) => ({ ...s, [userId]: "loading" }));
    try {
      await api.unfollow(userId);
      setFollowStates((s) => ({ ...s, [userId]: undefined }));
      toast.success("Vous ne suivez plus cet utilisateur");
    } catch (err) {
      setFollowStates((s) => ({ ...s, [userId]: "following" }));
      toast.error(err.message);
    }
  };

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-semibold mb-2">Rechercher</h1>
        <p className="text-muted-foreground">
          Trouvez des utilisateurs à suivre sur InFinea
        </p>
      </div>

      {/* Search input */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher par nom..."
          className="pl-12 h-12 rounded-xl text-base"
          autoFocus
        />
        {loading && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="rounded-xl border border-border divide-y divide-border">
          {results.map((user) => {
            const state = followStates[user.user_id];
            return (
              <UserCard
                key={user.user_id}
                user={user}
                isFollowing={state === "following"}
                onFollow={() => handleFollow(user.user_id)}
                onUnfollow={() => handleUnfollow(user.user_id)}
                loading={state === "loading"}
              />
            );
          })}
        </div>
      )}

      {/* Empty states */}
      {searched && results.length === 0 && !loading && (
        <div className="text-center py-16 text-muted-foreground">
          <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-1">Aucun résultat</p>
          <p className="text-sm">Essayez un autre nom ou terme de recherche.</p>
        </div>
      )}

      {!searched && !loading && (
        <div className="text-center py-16 text-muted-foreground">
          <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-1">Découvrez la communauté InFinea</p>
          <p className="text-sm">Tapez au moins 2 caractères pour lancer la recherche.</p>
        </div>
      )}
    </AppLayout>
  );
}
