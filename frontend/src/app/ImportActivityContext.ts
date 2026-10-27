import { createContext } from "react";

export const ImportActivityContext = createContext<{
  isImporting: boolean;
  setIsImporting: (isImporting: boolean) => void;
} | null>(null);
