"use client";
import { ReactNode } from "react";

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  noScroll = false,   // 👈 new prop
  bare = false,
}: {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  noScroll?: boolean;
  bare?: boolean;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-md flex justify-center items-center z-50">
      <div
        className={
          bare
            ? "relative flex flex-col items-center"
            : "bg-slate-800 rounded-lg p-6 max-w-md w-full text-white relative flex flex-col items"
        }
      >
        {!bare && title && <h2 className="text-xl font-bold mb-4">{title}</h2>}

        <div className={noScroll ? "" : "max-h-80 overflow-y-auto space-y-3"}>
          {children}
        </div>

        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-white"
        >
          ✕
        </button>
      </div>
    </div>
  );
}