import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Card, CardHeader, CardBody, Button, Avatar } from '@heroui/react';
import { useLogoutMutation } from '../features/auth/api/authApiSlice';
import { logout as clearAuthState } from '../features/auth/authSlice';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [logout, { isLoading }] = useLogoutMutation();

  const handleLogout = async () => {
    try {
      await logout().unwrap();
      // Clear auth state
      dispatch(clearAuthState());
      navigate('/'); // Redirect to login page
    } catch (err) {
      console.error('Failed to logout:', err);
      alert('Failed to logout. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 md:p-12 lg:p-16">
      <h1 className="text-4xl lg:text-5xl font-extrabold text-gray-900 mb-4">Profile</h1>
      <p className="text-lg text-gray-600 mb-10">Manage your account settings and preferences.</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card */}
        <Card className="lg:col-span-2 rounded-xl shadow-lg bg-white">
          <CardHeader className="p-6 border-b border-gray-200">
            <h3 className="text-2xl font-semibold text-gray-800">Account Information</h3>
          </CardHeader>
          <CardBody className="p-6">
            <div className="flex items-center space-x-4 mb-6">
              <Avatar
                name="User"
                className="w-20 h-20 text-lg"
                color="primary"
              />
              <div>
                <h4 className="text-xl font-semibold text-gray-800">User Account</h4>
                <p className="text-gray-600">HR Professional</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <h5 className="text-sm font-medium text-gray-500">Account Type</h5>
                <p className="mt-1 text-lg text-gray-900">HR Manager</p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <h5 className="text-sm font-medium text-gray-500">Account Status</h5>
                <p className="mt-1 text-lg text-green-600">Active</p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Actions Card */}
        <Card className="rounded-xl shadow-lg bg-white">
          <CardHeader className="p-6 border-b border-gray-200">
            <h3 className="text-2xl font-semibold text-gray-800">Account Actions</h3>
          </CardHeader>
          <CardBody className="p-6">
            <div className="space-y-4">
              <Button
                color="danger"
                variant="flat"
                size="lg"
                fullWidth
                onClick={handleLogout}
                isLoading={isLoading}
                className="py-3 text-lg font-semibold"
              >
                {isLoading ? 'Logging out...' : 'Logout'}
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default ProfilePage; 