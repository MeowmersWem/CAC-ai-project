import 'package:flutter/material.dart';
import 'class_search_page.dart';
import 'signup_page.dart';
import 'services/api_service.dart';
import 'my_classes_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      routes: {
        '/class-search': (context) => const ClassSearchPage(),
        '/sign-up': (context) => const SignUpPage(),
      },
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
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
  int _counter = 0;

  

 

  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;

 
  void _signIn() async {
  print("🔵 Sign in button pressed!");
  print("Email: ${_emailController.text}");
  print("Password length: ${_passwordController.text.length}");
  
  setState(() {
    _isLoading = true;
    _errorMessage = null;
  });

  try {
    print("🔵 Calling API login...");
    final result = await ApiService.login(
      _emailController.text,
      _passwordController.text,
    );
    
    print("🟢 Login successful! Result: $result");
    
    // Navigate to your existing My Classes page
    print("🔵 Navigating to MyClassesPage...");
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (context) => const MyClassesPage(),
      ),
    );
    print("🟢 Navigation complete!");
    
  } catch (e) {
    print("🔴 Login error: $e");
    setState(() {
      _errorMessage = 'Login failed: ${e.toString()}';
    });
  }

  setState(() {
    _isLoading = false;
  });
  print("🔵 Sign in process complete");
}
  
  void _showSignUpDialog() {
    showDialog(
      context: context,
      builder: (dialogContext) {
        final fullNameController = TextEditingController();
        final universityController = TextEditingController();
        final emailController = TextEditingController(text: _emailController.text);
        final passwordController = TextEditingController(text: _passwordController.text);
        bool isSubmitting = false;
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Create account'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: fullNameController,
                      decoration: const InputDecoration(labelText: 'Full name'),
                      textInputAction: TextInputAction.next,
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: universityController,
                      decoration: const InputDecoration(labelText: 'University'),
                      textInputAction: TextInputAction.next,
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: emailController,
                      decoration: const InputDecoration(labelText: 'Email'),
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: passwordController,
                      decoration: const InputDecoration(labelText: 'Password'),
                      obscureText: true,
                      textInputAction: TextInputAction.done,
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: isSubmitting ? null : () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: isSubmitting
                      ? null
                      : () async {
                          setStateDialog(() {
                            isSubmitting = true;
                          });
                          try {
                            await ApiService.signup(
                              emailController.text,
                              passwordController.text,
                              fullNameController.text,
                              universityController.text,
                            );
                            if (!mounted) return;
                            Navigator.of(dialogContext).pop();
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Account created! You can now sign in.')),
                            );
                          } catch (e) {
                            setStateDialog(() {
                              isSubmitting = false;
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Sign up failed: ${e.toString()}')),
                            );
                          }
                        },
                  child: isSubmitting
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Create account'),
                ),
              ],
            );
          },
        );
      },
    );
  }
   void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }

 

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
                          color: Colors.black.withOpacity(0.06),
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
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}
