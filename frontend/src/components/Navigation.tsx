import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Button } from '@heroui/react';

const Navigation: React.FC = () => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/';

  if (isAuthPage) {
    return null; // Don't show navigation on auth page
  }

  return (
    <Navbar className="bg-white shadow-sm">
      <NavbarBrand>
        <Link to="/dashboard" className="text-xl font-bold text-gray-900">
          CDEK HR Platform
        </Link>
      </NavbarBrand>

      <NavbarContent className="hidden sm:flex gap-4" justify="center">
        <NavbarItem isActive={location.pathname === '/dashboard'}>
          <Link
            to="/dashboard"
            className={`text-sm font-medium ${
              location.pathname === '/dashboard'
                ? 'text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Dashboard
          </Link>
        </NavbarItem>
      </NavbarContent>

      <NavbarContent justify="end">
        <NavbarItem>
          <Link to="/profile">
            <Button
              color="primary"
              variant="flat"
              className="text-sm font-medium"
            >
              Profile
            </Button>
          </Link>
        </NavbarItem>
      </NavbarContent>
    </Navbar>
  );
};

export default Navigation; 