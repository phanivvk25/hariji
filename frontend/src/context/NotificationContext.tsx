import React, { createContext, useContext, useState } from "react";
import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  Input,
  Text,
  Badge,
  Toaster,
  useToastController,
  useId,
  Toast,
  ToastTitle,
  ToastBody,
} from "@fluentui/react-components";
import {
  CheckmarkCircle24Filled,
  DismissCircle24Filled,
  Warning24Filled,
  Info24Filled,
} from "@fluentui/react-icons";

type IntentType = "success" | "error" | "warning" | "info";

interface DialogState {
  isOpen: boolean;
  type: "alert" | "confirm" | "prompt";
  title: string;
  message: string;
  intent: IntentType;
  inputValue?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: (val?: string) => void;
  onCancel?: () => void;
}

interface NotificationContextValue {
  notify: (title: string, message?: string, intent?: IntentType) => void;
  showAlert: (title: string, message?: string, intent?: IntentType) => void;
  showConfirm: (
    title: string,
    message: string,
    onConfirm: () => void,
    intent?: IntentType,
    confirmText?: string,
    cancelText?: string
  ) => void;
  showPrompt: (
    title: string,
    message: string,
    onConfirm: (value: string) => void,
    defaultValue?: string,
    confirmText?: string,
    cancelText?: string
  ) => void;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotification must be used within a NotificationProvider");
  }
  return context;
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const toasterId = useId("toaster");
  const { dispatchToast } = useToastController(toasterId);

  const [dialogState, setDialogState] = useState<DialogState>({
    isOpen: false,
    type: "alert",
    title: "",
    message: "",
    intent: "info",
  });

  const [promptValue, setPromptValue] = useState("");

  const getIntentIcon = (intent: IntentType) => {
    switch (intent) {
      case "success":
        return <CheckmarkCircle24Filled style={{ color: "#107C41" }} />;
      case "error":
        return <DismissCircle24Filled style={{ color: "#D13438" }} />;
      case "warning":
        return <Warning24Filled style={{ color: "#D83B01" }} />;
      case "info":
      default:
        return <Info24Filled style={{ color: "#0078D4" }} />;
    }
  };

  const getIntentBadgeColor = (intent: IntentType) => {
    switch (intent) {
      case "success":
        return "success";
      case "error":
        return "danger";
      case "warning":
        return "warning";
      case "info":
      default:
        return "brand";
    }
  };

  const notify = (title: string, message?: string, intent: IntentType = "info") => {
    dispatchToast(
      <Toast>
        <ToastTitle media={getIntentIcon(intent)}>{title}</ToastTitle>
        {message && <ToastBody>{message}</ToastBody>}
      </Toast>,
      { intent, timeout: 4000 }
    );
  };

  const showAlert = (title: string, message?: string, intent: IntentType = "info") => {
    setDialogState({
      isOpen: true,
      type: "alert",
      title,
      message: message || "",
      intent,
      confirmText: "OK",
    });
  };

  const showConfirm = (
    title: string,
    message: string,
    onConfirm: () => void,
    intent: IntentType = "warning",
    confirmText: string = "Confirm",
    cancelText: string = "Cancel"
  ) => {
    setDialogState({
      isOpen: true,
      type: "confirm",
      title,
      message,
      intent,
      confirmText,
      cancelText,
      onConfirm: () => onConfirm(),
      onCancel: () => {},
    });
  };

  const showPrompt = (
    title: string,
    message: string,
    onConfirm: (val: string) => void,
    defaultValue: string = "",
    confirmText: string = "Submit",
    cancelText: string = "Cancel"
  ) => {
    setPromptValue(defaultValue);
    setDialogState({
      isOpen: true,
      type: "prompt",
      title,
      message,
      intent: "info",
      confirmText,
      cancelText,
      onConfirm: (val) => onConfirm(val || ""),
      onCancel: () => {},
    });
  };

  const closeDialog = () => {
    setDialogState((prev) => ({ ...prev, isOpen: false }));
  };

  const handleConfirm = () => {
    if (dialogState.type === "prompt") {
      dialogState.onConfirm?.(promptValue);
    } else {
      dialogState.onConfirm?.();
    }
    closeDialog();
  };

  const handleCancel = () => {
    dialogState.onCancel?.();
    closeDialog();
  };

  return (
    <NotificationContext.Provider
      value={{ notify, showAlert, showConfirm, showPrompt }}
    >
      {children}
      <Toaster toasterId={toasterId} position="top-end" />

      {/* Fluent UI v2 Global Dialog for Alerts & Prompts */}
      <Dialog
        open={dialogState.isOpen}
        onOpenChange={(_, { open }) => !open && closeDialog()}
      >
        <DialogSurface style={{ maxWidth: 480 }}>
          <DialogBody>
            <DialogTitle>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {getIntentIcon(dialogState.intent)}
                <span>{dialogState.title}</span>
                <Badge
                  appearance="tint"
                  color={getIntentBadgeColor(dialogState.intent) as any}
                  size="small"
                >
                  {dialogState.intent.toUpperCase()}
                </Badge>
              </div>
            </DialogTitle>

            <DialogContent style={{ marginTop: 12 }}>
              {dialogState.message && (
                <Text size={300} style={{ whiteSpace: "pre-wrap", display: "block" }}>
                  {dialogState.message}
                </Text>
              )}

              {dialogState.type === "prompt" && (
                <div style={{ marginTop: 14 }}>
                  <Input
                    style={{ width: "100%" }}
                    value={promptValue}
                    onChange={(_, d) => setPromptValue(d.value)}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleConfirm();
                    }}
                  />
                </div>
              )}
            </DialogContent>

            <DialogActions style={{ marginTop: 20 }}>
              {dialogState.type !== "alert" && (
                <Button appearance="secondary" onClick={handleCancel}>
                  {dialogState.cancelText || "Cancel"}
                </Button>
              )}
              <Button
                appearance="primary"
                onClick={handleConfirm}
                style={
                  dialogState.intent === "error"
                    ? { backgroundColor: "#D13438" }
                    : dialogState.intent === "success"
                    ? { backgroundColor: "#107C41" }
                    : undefined
                }
              >
                {dialogState.confirmText || "OK"}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </NotificationContext.Provider>
  );
};
