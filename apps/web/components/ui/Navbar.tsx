"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { name: "Home", href: "/" },
  { name: "Search", href: "/search" },
  { name: "Profile", href: "/profile/demo" }, // temp profile route
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 py-3 flex justify-between items-center">
        <h1 className="text-xl font-bold text-indigo-600">GoodMusic 🎶</h1>
        <ul className="flex gap-6">
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`hover:text-indigo-500 ${
                  pathname === item.href ? "text-indigo-600 font-semibold" : ""
                }`}
              >
                {item.name}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}
