"use client";
import { Moon, Sun } from "lucide-react";

const KEY = "waymark.theme";

/** Light/dark switch. Stored choice wins; with none stored the OS preference applies (see globals.css). */
export default function ThemeToggle() {
  function flip() {
    const el = document.documentElement;
    const dark = el.dataset.theme === "dark" ||
      (!el.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    el.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem(KEY, el.dataset.theme); } catch {}
  }

  // Icon swap is pure CSS (see .theme-icon in globals.css), so there is no hydration state to sync.
  return (
    <button onClick={flip} aria-label="Toggle light/dark theme" title="Toggle theme"
      className="grid size-11 place-items-center rounded-lg border border-border bg-surface text-text">
      <Moon size={19} aria-hidden className="theme-icon-moon" />
      <Sun size={19} aria-hidden className="theme-icon-sun" />
    </button>
  );
}

/** Runs before paint (inline in <head>) so a stored theme never flashes the wrong colours. */
export const THEME_INIT = `try{var t=localStorage.getItem("${KEY}");if(t)document.documentElement.dataset.theme=t}catch(e){}`;
