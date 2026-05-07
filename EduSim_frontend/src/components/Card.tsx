import { motion } from "framer-motion";
import type { ReactNode } from "react";

export function Card({
  children,
  onClick,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ scale: 1.03, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`glass rounded-3xl p-6 cursor-pointer transition-shadow hover:neon-border group ${className}`}
    >
      {children}
    </motion.div>
  );
}

export function PageWrapper({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.35 }}
    >
      {children}
    </motion.div>
  );
}
