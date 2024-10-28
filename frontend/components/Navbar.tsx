"use client";

import {
  Archive,
  BarChart2,
  ExternalLink,
  Menu,
  MessageCircle,
  Send,
  Twitter,
  X,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

const Navbar = () => {
  const [timestamp, setTimestamp] = useState("");
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const updateTimestamp = () => {
      setTimestamp(new Date().toLocaleString());
    };

    updateTimestamp();
    const interval = setInterval(updateTimestamp, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-zinc-800 shadow-lg">
      {/* Main Navigation */}
      <div className=" mx-auto sm:px-6">
        <div className="flex justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center">
            <h2 className="text-purple-500 text-2xl font-bold">
              <Link href="/">Ducky&apos;s Stream of Thought</Link>
            </h2>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            <NavLinks />
            <div className="text-zinc-400">{timestamp}</div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-zinc-400 hover:text-white p-2"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden bg-zinc-800 shadow-lg">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <MobileNavLinks />
          </div>
          <div className="px-4 py-2 text-zinc-400 border-t border-zinc-700">
            {timestamp}
          </div>
        </div>
      )}
    </div>
  );
};

const NavLinks = () => (
  <div className="flex items-center space-x-6">
    <Link
      href="https://fatduck.ai"
      className="text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
    >
      <div className="flex items-center gap-2 justify-center">
        <span>Fatduck AI</span>
        <ExternalLink size={14} />
      </div>
    </Link>
    <Link
      href="https://twitter.com/duckunfiltered"
      className="text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
    >
      <Twitter size={18} />
      <span>Twitter</span>
    </Link>
    <Link
      href="https://t.me/DuckUnfiltered"
      className="text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
    >
      <Send size={18} />
      <span>Telegram</span>
    </Link>
    <Link
      href="/community"
      className="text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
    >
      <BarChart2 size={18} />
      <span>Community</span>
    </Link>
    <Link
      href="/archive"
      className="text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
    >
      <Archive size={18} />
      <span>Archive</span>
    </Link>
  </div>
);

const MobileNavLinks = () => (
  <div className="flex flex-col space-y-3">
    <Link
      href="https://fatduck.ai"
      className="text-zinc-400 hover:text-white flex items-center gap-2 p-2 rounded-md transition-colors"
    >
      <MessageCircle size={20} />
      <span>Fatduck AI</span>
      <ExternalLink size={16} />
    </Link>
    <Link
      href="https://twitter.com/duckunfiltered"
      className="text-zinc-400 hover:text-white flex items-center gap-2 p-2 rounded-md transition-colors"
    >
      <Twitter size={20} />
      <span>Twitter</span>
    </Link>
    <Link
      href="https://t.me/DuckUnfiltered"
      className="text-zinc-400 hover:text-white flex items-center gap-2 p-2 rounded-md transition-colors"
    >
      <Send size={20} />
      <span>Telegram</span>
    </Link>
    <Link
      href="/charts"
      className="text-zinc-400 hover:text-white flex items-center gap-2 p-2 rounded-md transition-colors"
    >
      <BarChart2 size={20} />
      <span>Charts</span>
    </Link>
    <Link
      href="/archive"
      className="text-zinc-400 hover:text-white flex items-center gap-2 p-2 rounded-md transition-colors"
    >
      <Archive size={20} />
      <span>Archive</span>
    </Link>
  </div>
);

export default Navbar;
