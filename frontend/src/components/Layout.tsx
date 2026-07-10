import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Video, 
  Scissors, 
  Settings, 
  LogOut,
  Menu,
  X 
} from 'lucide-react'
import { useState } from 'react'
import { User } from '../types'

interface LayoutProps {
  children: React.ReactNode
  user: User
  onLogout: () => void
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/vods', icon: Video, label: 'VODs' },
  { path: '/clips', icon: Scissors, label: 'Clips' },
  { path: '/settings', icon: Settings, label: 'Paramètres' },
]

export default function Layout({ children, user, onLogout }: LayoutProps) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-twitch-gray border-r border-gray-700
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-700">
          <Link to="/" className="flex items-center gap-3">
            <img src="/nexus.svg" alt="Nexus" className="w-8 h-8" />
            <span className="text-xl font-bold bg-gradient-to-r from-twitch-purple to-pink-500 bg-clip-text text-transparent">
              Nexus
            </span>
          </Link>
          <button 
            className="lg:hidden p-2 hover:bg-gray-700 rounded-lg"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path
            return (
              <Link
                key={path}
                to={path}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  ${isActive 
                    ? 'bg-twitch-purple text-white' 
                    : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }
                `}
              >
                <Icon size={20} />
                <span>{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* User */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <div className="flex items-center gap-3 mb-4">
            {user.profile_image ? (
              <img 
                src={user.profile_image} 
                alt={user.display_name}
                className="w-10 h-10 rounded-full"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-twitch-purple flex items-center justify-center">
                {user.display_name.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{user.display_name}</p>
              <p className="text-sm text-gray-400 truncate">@{user.login}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <header className="lg:hidden h-16 flex items-center justify-between px-4 border-b border-gray-700 bg-twitch-gray">
          <button 
            className="p-2 hover:bg-gray-700 rounded-lg"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>
          <img src="/nexus.svg" alt="Nexus" className="w-8 h-8" />
          <div className="w-10" />
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
