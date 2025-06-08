import React, { useState } from 'react';
import { useRegisterMutation, useLoginMutation } from '../features/auth/api/authApiSlice';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Input, Button, Link, Card, CardBody, CardHeader } from '@heroui/react';
import { setCredentials } from '../features/auth/authSlice';

const AuthPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [register, { isLoading: isRegistering }] = useRegisterMutation();
  const [login, { isLoading: isLoggingIn }] = useLoginMutation();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();

  // Get the redirect path from location state or default to dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isRegister) {
        await register({ email, password }).unwrap();
        alert('Registration successful! Please log in.');
        setIsRegister(false); // Switch to login after registration
      } else {
        const result = await login({ email, password }).unwrap();
        // Set authentication state
        dispatch(setCredentials({ email }));
        alert('Login successful!');
        navigate(from, { replace: true }); // Navigate to the attempted page or dashboard
      }
    } catch (err: any) {
      console.error('Failed to process request:', err);
      alert(`Error: ${err.data?.detail || 'Something went wrong'}`);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-blue-100 via-purple-100 to-pink-100 p-4">
      <Card className="w-full max-w-md rounded-xl shadow-2xl overflow-hidden backdrop-blur-sm bg-white/70 animate-fade-in">
        <CardHeader className="flex flex-col gap-2 p-8 text-center bg-blue-600 text-white">
          <h2 className="text-4xl font-extrabold">
            {isRegister ? 'Create Account' : 'Welcome Back'}
          </h2>
          <p className="text-blue-200 text-base mt-2">
            {isRegister ? 'Join us and unlock a world of possibilities' : 'Sign in to continue to your dashboard'}
          </p>
        </CardHeader>
        <CardBody className="p-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <Input
              type="email"
              label="Email Address"
              placeholder="Enter your email"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
              size="lg"
              fullWidth
              className="focus:ring-blue-500 focus:border-blue-500"
            />
            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              required
              size="lg"
              fullWidth
              className="focus:ring-blue-500 focus:border-blue-500"
            />
            <Button
              type="submit"
              color="primary"
              size="lg"
              fullWidth
              isLoading={isRegistering || isLoggingIn}
              disabled={isRegistering || isLoggingIn}
              className="mt-4 py-3 text-lg font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105"
            >
              {isRegister ? 'Register Account' : 'Login to Dashboard'}
            </Button>
          </form>
          <p className="mt-8 text-center text-gray-700 text-base">
            {isRegister ? 'Already have an account? ' : "Don't have an account? "}
            <Link
              onClick={() => setIsRegister(!isRegister)}
              className="text-blue-700 font-bold cursor-pointer hover:underline transition-colors duration-200"
            >
              {isRegister ? 'Login here' : 'Register here'}
            </Link>
          </p>
        </CardBody>
      </Card>
    </div>
  );
};

export default AuthPage; 