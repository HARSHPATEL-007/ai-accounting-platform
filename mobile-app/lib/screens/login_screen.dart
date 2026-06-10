import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _secureStorage = const FlutterSecureStorage();
  final _localAuth = LocalAuthentication();
  bool _isLoading = false;

  Future<void> _login() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    await _secureStorage.write(key: 'auth_token', value: 'dummy_token');
    await _secureStorage.write(key: 'user_id', value: 'user_123');
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/dashboard');
    }
    setState(() => _isLoading = false);
  }

  Future<void> _authenticateWithBiometric() async {
    try {
      final isAvailable = await _localAuth.canCheckBiometrics;
      if (!isAvailable) return;

      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Authenticate to access your accounting data',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );

      if (didAuthenticate) {
        await _secureStorage.write(key: 'auth_token', value: 'biometric_token');
        if (mounted) {
          Navigator.pushReplacementNamed(context, '/dashboard');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Biometric authentication failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.account_balance, size: 80, color: Colors.blue),
              const SizedBox(height: 24),
              const Text(
                'Accounting Platform',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                'Secure. Automated. Compliant.',
                style: TextStyle(color: Colors.grey[600]),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                decoration: const InputDecoration(
                  labelText: 'Password',
                  prefixIcon: Icon(Icons.lock),
                  border: OutlineInputBorder(),
                ),
                obscureText: true,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  child: _isLoading
                      ? const CircularProgressIndicator()
                      : const Text('Login'),
                ),
              ),
              const SizedBox(height: 16),
              TextButton.icon(
                onPressed: _authenticateWithBiometric,
                icon: const Icon(Icons.fingerprint),
                label: const Text('Login with Biometric'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
