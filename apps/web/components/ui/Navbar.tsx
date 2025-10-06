"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.push("/login");
  }  
  
  const navItems = [
    { href: "/", label: "Home" },
    { href: "/search", label: "Search" },
    ...(user
      ? [{ href: `/profile/${user.username}`, label: "Profile" }]
      : [
          { href: "/login", label: "Login" },
          { href: "/register", label: "Register" },
        ]),
  ];

  return (
    <nav className="bg-gray-900 shadow-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto relative flex items-center px-6 py-3">
      {/* Left: Logo */}
      <Link href="/" className="text-3xl font-extrabold">
        <span className="bg-gradient-to-r from-pink-500 via-purple-400 to-indigo-100 bg-clip-text text-transparent">
          GoodMusic
        </span>{" "}
        🎶
      </Link>

      {/* Center: Nav links */}
      <ul className="absolute left-1/2 -translate-x-1/2 flex gap-10 text-gray-200 text-lg font-medium">
        {navItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={`hover:text-indigo-400 transition ${
                pathname === item.href ? "text-indigo-400 font-semibold" : ""
              }`}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>

      {/* Right: Logout */}
      {user && (
        <button
          onClick={handleLogout}
          className="ml-auto text-gray-200 hover:text-red-400 transition text-base font-medium"
        >
          Logout
        </button>
      )}
      </div>
    </nav>
  );
}