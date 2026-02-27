import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Sparkles, Loader2, Check, Plus } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

export default function CreateActionModal({ open, onOpenChange, onActionCreated }) {
  const [description, setDescription] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAction, setGeneratedAction] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleGenerate = async () => {
    if (!description.trim()) {
      toast.error("Décrivez l'action que vous souhaitez créer");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await authFetch(`${API}/ai/create-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: description.trim() }),
      });

      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setGeneratedAction(data.action || data);
    } catch (error) {
      toast.error("Erreur lors de la génération de l'action");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = () => {
    // The action is already saved by the backend on creation
    toast.success("Action ajoutée à votre bibliothèque !");
    onActionCreated?.();
    handleClose();
  };

  const handleClose = () => {
    setDescription("");
    setGeneratedAction(null);
    onOpenChange(false);
  };

  const categoryLabels = {
    learning: "Apprentissage",
    productivity: "Productivité",
    well_being: "Bien-être",
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Créer une action personnalisée
          </DialogTitle>
          <DialogDescription>
            Décrivez ce que vous voulez faire, l'IA créera une micro-action sur mesure.
          </DialogDescription>
        </DialogHeader>

        {!generatedAction ? (
          <div className="py-4 space-y-4">
            <Textarea
              placeholder="Ex: Je veux apprendre 5 mots de vocabulaire anglais en 3 minutes..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-24 resize-none"
              data-testid="action-description-input"
            />
            <Button
              onClick={handleGenerate}
              className="w-full h-11 rounded-xl"
              disabled={isGenerating || !description.trim()}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Génération en cours...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Générer avec l'IA
                </>
              )}
            </Button>
          </div>
        ) : (
          <div className="py-4 animate-fade-in">
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-heading font-semibold">{generatedAction.title}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {categoryLabels[generatedAction.category] || generatedAction.category}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{generatedAction.description}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{generatedAction.duration_min}-{generatedAction.duration_max} min</span>
                  <span>•</span>
                  <span className="capitalize">{generatedAction.energy_level}</span>
                </div>
                {generatedAction.instructions?.length > 0 && (
                  <div className="pt-2 border-t border-border">
                    <p className="text-xs text-muted-foreground mb-2">Instructions :</p>
                    <ol className="space-y-1">
                      {generatedAction.instructions.map((step, i) => (
                        <li key={i} className="text-sm flex items-start gap-2">
                          <span className="text-xs text-muted-foreground mt-0.5">{i + 1}.</span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        <DialogFooter>
          {generatedAction ? (
            <div className="flex gap-2 w-full">
              <Button variant="outline" onClick={() => setGeneratedAction(null)} className="flex-1">
                Modifier
              </Button>
              <Button onClick={handleSave} disabled={isSaving} className="flex-1">
                <Check className="w-4 h-4 mr-2" />
                Ajouter
              </Button>
            </div>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              Annuler
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
