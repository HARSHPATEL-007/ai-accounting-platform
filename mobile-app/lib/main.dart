import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:accounting_platform_mobile/providers/auth_provider.dart';
import 'package:accounting_platform_mobile/providers/connectivity_provider.dart';
import 'package:accounting_platform_mobile/screens/splash_screen.dart';
import 'package:accounting_platform_mobile/screens/login_screen.dart';
import 'package:accounting_platform_mobile/screens/dashboard_screen.dart';
import 'package:accounting_platform_mobile/services/sync_service.dart';
import 'package:accounting_platform_mobile/services/notification_service.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  const AndroidInitializationSettings initializationSettingsAndroid =
      AndroidInitializationSettings('@mipmap/ic_launcher');
  const DarwinInitializationSettings initializationSettingsIOS =
      DarwinInitializationSettings();
  const InitializationSettings initializationSettings = InitializationSettings(
    android: initializationSettingsAndroid,
    iOS: initializationSettingsIOS,
  );
  await flutterLocalNotificationsPlugin.initialize(initializationSettings);

  await SyncService().initialize();

  runApp(const AccountingPlatformApp());
}

class AccountingPlatformApp extends StatelessWidget {
  const AccountingPlatformApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => AuthProvider()),
        BlocProvider(create: (_) => ConnectivityProvider()),
      ],
      child: MaterialApp(
        title: 'Accounting Platform',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2563EB),
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          fontFamily: 'Inter',
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2563EB),
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
          fontFamily: 'Inter',
        ),
        home: const SplashScreen(),
        routes: {
          '/login': (context) => const LoginScreen(),
          '/dashboard': (context) => const DashboardScreen(),
        },
      ),
    );
  }
}
