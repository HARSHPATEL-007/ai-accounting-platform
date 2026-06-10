import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  Future<void> _logout(BuildContext context) async {
    const storage = FlutterSecureStorage();
    await storage.deleteAll();
    if (context.mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        const ListTile(
          leading: Icon(Icons.person),
          title: Text('Profile'),
          subtitle: Text('Manage your account details'),
        ),
        const ListTile(
          leading: Icon(Icons.notifications),
          title: Text('Notifications'),
          subtitle: Text('GST deadlines, tax reminders'),
        ),
        const ListTile(
          leading: Icon(Icons.security),
          title: Text('Security'),
          subtitle: Text('Biometric login, 2FA'),
        ),
        const ListTile(
          leading: Icon(Icons.cloud_off),
          title: Text('Offline Mode'),
          subtitle: Text('Sync settings, data usage'),
        ),
        const Divider(),
        ListTile(
          leading: const Icon(Icons.logout, color: Colors.red),
          title: const Text('Logout', style: TextStyle(color: Colors.red)),
          onTap: () => _logout(context),
        ),
        const Padding(
          padding: EdgeInsets.all(16),
          child: Text(
            'AI-generated responses are for informational purposes only. Consult a licensed CA before making decisions.',
            style: TextStyle(fontSize: 12, color: Colors.grey),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}
