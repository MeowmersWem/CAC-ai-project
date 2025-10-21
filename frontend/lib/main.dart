import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'class_search_page.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'signup_page.dart';
import 'services/api_service.dart';
import 'my_classes_page.dart';
import 'in_class_page.dart';
import 'start_page.dart';
import 'theme_controller.dart';
import 'instructor_my_classes_page.dart';
import 'ai_page.dart';
import 'grades_page.dart';
import 'notes_page.dart';
import 'account_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: ThemeController.instance.themeMode,
      builder: (context, mode, _) {
        return ValueListenableBuilder<double>(
          valueListenable: ThemeController.instance.textScaleFactor,
          builder: (context, scale, __) {
            return ValueListenableBuilder<Locale?>(
              valueListenable: ThemeController.instance.locale,
              builder: (context, appLocale, ___) {
                return MediaQuery(
                  data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(scale)),
                  child: MaterialApp(
          title: 'Flutter Demo',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.deepPurple,
              brightness: Brightness.light,
            ),
          ),
          darkTheme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.deepPurple,
              brightness: Brightness.dark,
            ),
          ),
          themeMode: mode,
          locale: appLocale,
          supportedLocales: const [
            Locale('en'), // English
            Locale('zh', 'CN'), // Simplified Chinese
            Locale('fr'), // French
          ],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          routes: {
        '/class-search': (context) => const ClassSearchPage(),
        '/sign-up': (context) => const SignUpPage(),
        '/my-classes': (context) => const MyClassesPage(),
        // Student routes for bottom nav
        '/ai': (context) => const AIPage(isInstructor: false),
        '/grades': (context) => const GradesPage(isInstructor: false),
        '/notes': (context) => const NotesPage(isInstructor: false),
        '/account': (context) => const AccountPage(isInstructor: false),
        // Instructor routes
        '/instructor/my-classes': (context) {
          final email = ModalRoute.of(context)?.settings.arguments as String? ?? '';
          return InstructorMyClassesPage(email: email);
        },
        '/instructor/ai': (context) => const AIPage(isInstructor: true),
        '/instructor/grades': (context) => const GradesPage(isInstructor: true),
        '/instructor/notes': (context) => const NotesPage(isInstructor: true),
        '/instructor/account': (context) => const AccountPage(isInstructor: true),
        '/in-class': (context) {
          // Fallback demo route with placeholder ids
          return const InClassPage(classId: 'demo-class', className: 'Class');
        },
          },
          home: const MyHomePage(title: 'Flutter Demo Home Page'),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

 
  void _signIn() async {
  // basic email format check before calling backend
  final email = _emailController.text.trim();
  final emailRegex = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  if (!emailRegex.hasMatch(email)) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a valid email address')));
    return;
  }
  debugPrint("🔵 Sign in button pressed!");
  debugPrint("Email: $email");
  debugPrint("Password length: ${_passwordController.text.length}");
  
  setState(() {
    _isLoading = true;
  });

  try {
    debugPrint("🔵 Calling API login...");
    final result = await ApiService.login(
      _emailController.text,
      _passwordController.text,
    );
    
    debugPrint("🟢 Login successful! Result: $result");
    
    // After login, decide where to go based on profile completeness
    try {
      final profile = await ApiService.getProfile(email: _emailController.text.trim());
      final String? role = profile['role'];
      final String? university = profile['university'];
      final String? state = profile['state'];
      final bool needsProfile =
          (role == null || role.isEmpty) ||
          (university == null || university.isEmpty) ||
          (state == null || state.isEmpty);
      if (!mounted) return;
      if (needsProfile) {
        debugPrint("🔵 Navigating to StartPage (collect role/school/state)...");
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => StartPage(email: _emailController.text.trim())),
        );
      } else {
        // role is guaranteed non-null here due to needsProfile == false
        if (role.toLowerCase() == 'instructor') {
          Navigator.of(context).pushReplacementNamed(
            '/instructor/my-classes',
            arguments: _emailController.text.trim(),
          );
        } else {
          debugPrint("🔵 Role=student → go to MyClassesPage...");
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => const MyClassesPage()),
          );
        }
      }
    } catch (e) {
      // If profile fetch fails, fallback to StartPage so user can complete info
      if (!mounted) return;
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => StartPage(email: _emailController.text.trim())),
          );
    }
    debugPrint("🟢 Navigation complete!");
    
  } catch (e) {
    debugPrint("🔴 Login error: $e");
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Login failed: ${e.toString()}')));
  }

  setState(() {
    _isLoading = false;
  });
  debugPrint("🔵 Sign in process complete");
}
  
  // Removed unused sign-up dialog and counter

 

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: 'Search Classes',
            onPressed: () {
              Navigator.of(context).pushNamed('/class-search');
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
        children: [
          Expanded(
            flex: 1,
            child: Align(
              alignment: const Alignment(0, -0.5),
              child: Builder(
                builder: (context) {
                  final TextStyle baseTextStyle = DefaultTextStyle.of(context).style;
                  final double baseFontSize = baseTextStyle.fontSize ?? Theme.of(context).textTheme.bodyMedium?.fontSize ?? 14.0;
                  return Text(
                    'Collaborative Learning,\nJust a Click Away',
                    textAlign: TextAlign.center,
                    style: baseTextStyle.copyWith(
                      fontSize: baseFontSize * 2,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                },
              ),
            ),
          ),
          Expanded(
            flex: 1,
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 360),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: Colors.black),
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.06),
                          blurRadius: 12,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        
                        const SizedBox(height: 12),
                        TextField(
                          controller: _emailController, // Add this line
                          decoration: InputDecoration(
                            labelText: 'Email',
                            prefixIcon: const Icon(Icons.email_outlined),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            isDense: true,
                          ),
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                        ), 
                        TextField(
                          controller: _passwordController,
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            isDense: true,
                          ),
                          obscureText: true,
                          textInputAction: TextInputAction.done,
                        ), 
                         
                        const SizedBox(height: 16),
                        SizedBox(
                          height: 48,
                          child:  ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.black,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                              textStyle: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            onPressed: _isLoading ? null : _signIn, // Change this line
                            child: _isLoading 
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Sign In'), // Keep your existing text
                          ),
                        ),
                        const SizedBox(height: 8),
                        Align(
                          alignment: Alignment.center,
                          child: TextButton(
                            onPressed: () {},
                            style: TextButton.styleFrom(
                              foregroundColor: Colors.black,
                              textStyle: Theme.of(context).textTheme.bodySmall,
                            ),
                            child: const Text('Forgot password'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            flex: 1,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 360),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      SizedBox(
                        height: 48,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.black,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            textStyle: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          onPressed: () {},
                          child: const Text('Sign in with Google'),
                        ),
                      ),
                      const SizedBox(height: 8),
                      GestureDetector(
                        onTap: () {
                          Navigator.of(context).pushNamed('/sign-up');
                        },
                        child: Container(
                          height: 48,
                          decoration: BoxDecoration(
                            color: Color(0xFFFFE0F0),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.pinkAccent),
                          ),
                          alignment: Alignment.center,
                          child: const Text(
                            'Sign up',
                            style: TextStyle(
                              color: Colors.black,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      ),
      // Floating action button removed as counter is unused
    );
  }
}
