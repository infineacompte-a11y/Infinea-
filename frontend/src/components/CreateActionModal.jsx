import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { VoiceTextArea } from "@/components/VoiceInput";
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
  const { t } = useTranslation();
  const [description, setDescription] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAction, setGeneratedAction] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleGenerate = async () => {
    if (!description.trim()) {
      toast.error(t("components.createAction.errorEmpty"));
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
      toast.error(t("components.createAction.errorGenerate"));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = () => {
    // The action is already saved by the backend on creation
    toast.success(t("components.createAction.successAdded"));
    onActionCreated?.();
    handleClose();
  };

  const handleClose = () => {
    setDescription("");
    setGeneratedAction(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            {t("components.createAction.title")}
          </DialogTitle>
          <DialogDescription>
            {t("components.createAction.description")}
          </DialogDescription>
        </DialogHeader>

        {!generatedAction ? (
          <div className="py-4 space-y-4">
            <VoiceTextArea
              value={description}
              onChange={setDescription}
              placeholder={t("components.createAction.placeholder")}
              rows={3}
            />
            <Button
              onClick={handleGenerate}
              className="w-full h-11 rounded-xl"
              disabled={isGenerating || !description.trim()}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  {t("components.createAction.generating")}
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  {t("components.createAction.generateButton")}
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
                    {t(`categories.${generatedAction.category}`, generatedAction.category)}
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
                    <p className="text-xs text-muted-foreground mb-2">{t("components.createAction.instructions")}</p>
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
                {t("components.createAction.modify")}
              </Button>
              <Button onClick={handleSave} disabled={isSaving} className="flex-1">
                <Check className="w-4 h-4 mr-2" />
                {t("components.createAction.add")}
              </Button>
            </div>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              {t("common.cancel")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
