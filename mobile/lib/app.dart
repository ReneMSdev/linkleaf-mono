import 'package:flutter/material.dart';
import 'core/theme.dart';
import 'core/router.dart';

class LinkLeafApp extends StatelessWidget {
  const LinkLeafApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LinkLeaf',
      theme: AppTheme.light,
      initialRoute: AppRouter.login,
      routes: AppRouter.routes,
    );
  }
}
