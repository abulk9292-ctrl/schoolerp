import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

void main() {
  runApp(const MyApp());
}

const String baseUrl = 'https://alrahman-erp.onrender.com';
// Android phone এ run করলে পরে এটা PC IP দিয়ে change করবে
// Example: http://192.168.0.105:8000

class AppColors {
  static const Color bg = Color(0xFFF3F5F8);
  static const Color dark = Color(0xFF081B33);
  static const Color dark2 = Color(0xFF0D2342);
  static const Color green = Color(0xFF38D27A);
  static const Color greenDark = Color(0xFF28B866);
  static const Color white = Colors.white;
  static const Color textDark = Color(0xFF0F172A);
  static const Color textLight = Color(0xFF64748B);
  static const Color red = Color(0xFFEF4444);
  static const Color orange = Color(0xFFF59E0B);
  static const Color blue = Color(0xFF2563EB);
  static const Color border = Color(0xFFE5E7EB);
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AL RAHMAN MISSION ERP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: AppColors.bg,
        useMaterial3: true,
        fontFamily: 'Arial',
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.green,
          brightness: Brightness.light,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: AppColors.green, width: 1.5),
          ),
        ),
      ),
      home: const LoginPage(),
    );
  }
}

class AppSession {
  static String token = '';
  static String username = '';
}

class UiHelpers {
  static BoxDecoration cardDecoration({
    Color color = Colors.white,
    double radius = 22,
  }) {
    return BoxDecoration(
      color: color,
      borderRadius: BorderRadius.circular(radius),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.05),
          blurRadius: 18,
          offset: const Offset(0, 8),
        ),
      ],
    );
  }

  static Widget sectionTitle(String title, {String? subtitle}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w800,
            color: AppColors.textDark,
          ),
        ),
        if (subtitle != null) ...[
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: const TextStyle(
              fontSize: 14,
              color: AppColors.textLight,
            ),
          ),
        ],
      ],
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController usernameController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();

  bool isLoading = false;
  String message = '';

  Future<void> login() async {
    setState(() {
      isLoading = true;
      message = '';
    });

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/mobile-api/login/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': usernameController.text.trim(),
          'password': passwordController.text.trim(),
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        AppSession.token = data['token'] ?? '';
        AppSession.username = data['username'] ?? '';

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const DashboardPage()),
        );
      } else {
        setState(() {
          message = data['message'] ?? 'Login failed';
        });
      }
    } catch (e) {
      setState(() {
        message = 'Server connection error: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Widget loginCard() {
    return Container(
      width: 420,
      padding: const EdgeInsets.all(28),
      decoration: UiHelpers.cardDecoration(color: Colors.white),
      child: Column(
        children: [
          Container(
            height: 68,
            width: 68,
            decoration: BoxDecoration(
              color: AppColors.green.withOpacity(0.12),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.school_rounded,
              color: AppColors.greenDark,
              size: 34,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'AL RAHMAN MISSION ERP',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const Text(
            'Teacher / Staff Login Panel',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textLight,
            ),
          ),
          const SizedBox(height: 28),
          TextField(
            controller: usernameController,
            decoration: const InputDecoration(
              labelText: 'Username',
              prefixIcon: Icon(Icons.person_outline),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: passwordController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'Password',
              prefixIcon: Icon(Icons.lock_outline),
            ),
          ),
          const SizedBox(height: 22),
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton(
              onPressed: isLoading ? null : login,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.green,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
              child: isLoading
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Login',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
            ),
          ),
          if (message.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              message,
              style: const TextStyle(
                color: AppColors.red,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
          ]
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF4F7FB), Color(0xFFEFF6F1)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: loginCard(),
          ),
        ),
      ),
    );
  }
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool isLoading = true;
  String message = '';

  String teacherPresent = '0';
  String teacherAbsent = '0';
  String teacherLate = '0';
  String teacherTotal = '0';

  String studentPresent = '0';
  String studentAbsent = '0';
  String studentLate = '0';
  String studentTotal = '0';

  String reportDate = '';

  @override
  void initState() {
    super.initState();
    fetchSummary();
  }

  Future<void> fetchSummary() async {
    setState(() {
      isLoading = true;
      message = '';
    });

    try {
      final headers = {
        'Authorization': 'Token ${AppSession.token}',
      };

      final teacherResponse = await http.get(
        Uri.parse('$baseUrl/mobile-api/teacher-attendance-summary/'),
        headers: headers,
      );

      final teacherData = jsonDecode(teacherResponse.body);

      if (teacherResponse.statusCode == 200 &&
          teacherData['status'] == 'success') {
        teacherPresent = teacherData['summary']['present'].toString();
        teacherAbsent = teacherData['summary']['absent'].toString();
        teacherLate = teacherData['summary']['late'].toString();
        teacherTotal = teacherData['summary']['total'].toString();
        reportDate = teacherData['date'].toString();
      }

      try {
        final studentResponse = await http.get(
          Uri.parse('$baseUrl/mobile-api/student-attendance-summary/'),
          headers: headers,
        );

        final studentData = jsonDecode(studentResponse.body);

        if (studentResponse.statusCode == 200 &&
            studentData['status'] == 'success') {
          studentPresent = studentData['summary']['present'].toString();
          studentAbsent = studentData['summary']['absent'].toString();
          studentLate = studentData['summary']['late'].toString();
          studentTotal = studentData['summary']['total'].toString();

          if (reportDate.isEmpty) {
            reportDate = studentData['date'].toString();
          }
        }
      } catch (_) {}

      if (teacherResponse.statusCode != 200 &&
          teacherTotal == '0' &&
          studentTotal == '0') {
        message = teacherData['message'] ?? 'Failed to load summary';
      }
    } catch (e) {
      setState(() {
        message = 'Summary load error: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void logout() {
    AppSession.token = '';
    AppSession.username = '';
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
    );
  }

Widget topBanner() {
  return Container(
    width: double.infinity,
    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 20),
    decoration: UiHelpers.cardDecoration(color: AppColors.dark, radius: 26),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final bool isSmall = constraints.maxWidth < 520;

        if (isSmall) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 26,
                    backgroundColor: AppColors.green,
                    child: Text(
                      AppSession.username.isNotEmpty
                          ? AppSession.username[0].toUpperCase()
                          : 'A',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        fontSize: 22,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Text(
                      'Hello ${AppSession.username} 👋',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                reportDate.isNotEmpty
                    ? 'Attendance overview for $reportDate'
                    : 'Your daily attendance dashboard',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.75),
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _bannerAction(
                      icon: Icons.refresh,
                      label: 'Refresh',
                      onTap: fetchSummary,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _bannerAction(
                      icon: Icons.logout,
                      label: 'Logout',
                      onTap: logout,
                    ),
                  ),
                ],
              ),
            ],
          );
        }

        return Row(
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: AppColors.green,
              child: Text(
                AppSession.username.isNotEmpty
                    ? AppSession.username[0].toUpperCase()
                    : 'A',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 22,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Hello ${AppSession.username} 👋',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    reportDate.isNotEmpty
                        ? 'Attendance overview for $reportDate'
                        : 'Your daily attendance dashboard',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.75),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                _bannerAction(
                  icon: Icons.refresh,
                  label: 'Refresh',
                  onTap: fetchSummary,
                ),
                _bannerAction(
                  icon: Icons.logout,
                  label: 'Logout',
                  onTap: logout,
                ),
              ],
            ),
          ],
        );
      },
    ),
  );
}

  Widget _bannerAction({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.08),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.white, size: 18),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget statCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
    bool active = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: UiHelpers.cardDecoration(
        color: active ? color : Colors.white,
        radius: 22,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                height: 52,
                width: 52,
                decoration: BoxDecoration(
                  color: active
                      ? Colors.white.withOpacity(0.18)
                      : color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(
                  icon,
                  color: active ? Colors.white : color,
                  size: 28,
                ),
              ),
              const Spacer(),
              Icon(
                Icons.more_horiz,
                color: active ? Colors.white70 : AppColors.textLight,
              )
            ],
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              color: active ? Colors.white : AppColors.textDark,
              fontSize: 30,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: TextStyle(
              color: active ? Colors.white70 : AppColors.textLight,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget panelCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: UiHelpers.cardDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                height: 52,
                width: 52,
                decoration: BoxDecoration(
                  color: AppColors.green.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: AppColors.greenDark, size: 28),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: AppColors.textLight,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              )
            ],
          ),
          const SizedBox(height: 20),
          ...children,
        ],
      ),
    );
  }

  Widget actionButton({
    required String title,
    required IconData icon,
    required VoidCallback onTap,
    Color bg = AppColors.dark,
    Color fg = Colors.white,
  }) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton.icon(
        onPressed: onTap,
        icon: Icon(icon),
        label: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: bg,
          foregroundColor: fg,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }

  Widget teacherOwnAttendancePanel() {
    return panelCard(
      title: 'Teacher Own Attendance',
      subtitle: 'Mark your daily attendance with selfie and live location',
      icon: Icons.verified_user_rounded,
      children: [
        Row(
          children: [
            Expanded(
              child: _infoTile('Login User', AppSession.username),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _infoTile(
                'Summary Date',
                reportDate.isEmpty ? 'Today' : reportDate,
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: _smallStatBox(
                'Present',
                teacherPresent,
                AppColors.greenDark,
                Icons.check_circle,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _smallStatBox(
                'Late',
                teacherLate,
                AppColors.orange,
                Icons.access_time,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        actionButton(
          title: 'Open Teacher Attendance Panel',
          icon: Icons.camera_alt_outlined,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const AttendancePage()),
            );
          },
          bg: AppColors.green,
        ),
        const SizedBox(height: 12),
        actionButton(
          title: 'Open Teacher Report',
          icon: Icons.description_outlined,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const TeacherReportPage()),
            );
          },
          bg: AppColors.dark,
        ),
      ],
    );
  }

  Widget studentAttendancePanel() {
    return panelCard(
      title: 'Student Attendance Panel',
      subtitle: 'Student attendance overview, marking and report access',
      icon: Icons.groups_rounded,
      children: [
        Row(
          children: [
            Expanded(
              child: _smallStatBox(
                'Total Students',
                studentTotal,
                AppColors.dark,
                Icons.school_rounded,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _smallStatBox(
                'Present Today',
                studentPresent,
                AppColors.greenDark,
                Icons.check_circle_rounded,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _smallStatBox(
                'Absent Today',
                studentAbsent,
                AppColors.red,
                Icons.person_off_rounded,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _smallStatBox(
                'Late Today',
                studentLate,
                AppColors.orange,
                Icons.access_time_rounded,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.bg,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Student Panel Ready',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textDark,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                reportDate.isEmpty
                    ? 'Student attendance summary load হয়নি। API add করলে এখানে live data আসবে।'
                    : 'Today: $reportDate • Total: $studentTotal • Present: $studentPresent • Absent: $studentAbsent • Late: $studentLate',
                style: const TextStyle(
                  color: AppColors.textLight,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        actionButton(
          title: 'QR Scan Student Attendance',
          icon: Icons.qr_code_scanner_rounded,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const QRStudentAttendancePage()),
            );
          },
          bg: AppColors.blue,
        ),
        const SizedBox(height: 12),
        actionButton(
          title: 'Open Student Attendance Panel',
          icon: Icons.fact_check_outlined,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const StudentAttendancePage()),
            );
          },
          bg: AppColors.green,
        ),
        const SizedBox(height: 12),
        actionButton(
          title: 'Open Student Report',
          icon: Icons.description_outlined,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const StudentReportPage()),
            );
          },
          bg: AppColors.dark,
        ),
      ],
    );
  }

  Widget _smallStatBox(
    String title,
    String value,
    Color color,
    IconData icon,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withOpacity(0.16)),
      ),
      child: Row(
        children: [
          Container(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
              color: color.withOpacity(0.14),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textDark,
                  ),
                ),
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.textLight,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoTile(String title, String value) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: AppColors.textLight,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.textDark,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget desktopDashboard() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1320),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            topBanner(),
            const SizedBox(height: 22),
            if (isLoading)
              const Padding(
                padding: EdgeInsets.all(30),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (message.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: UiHelpers.cardDecoration(),
                child: Text(
                  message,
                  style: const TextStyle(
                    color: AppColors.red,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              )
            else ...[
              GridView.count(
                crossAxisCount: 4,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 1.35,
                children: [
                  statCard(
                    title: 'TOTAL TEACHERS',
                    value: teacherTotal,
                    icon: Icons.groups_rounded,
                    color: AppColors.dark,
                  ),
                  statCard(
                    title: 'PRESENT TODAY',
                    value: teacherPresent,
                    icon: Icons.login_rounded,
                    color: AppColors.green,
                    active: true,
                  ),
                  statCard(
                    title: 'ABSENT TODAY',
                    value: teacherAbsent,
                    icon: Icons.sentiment_dissatisfied_rounded,
                    color: AppColors.red,
                  ),
                  statCard(
                    title: 'LATE TODAY',
                    value: teacherLate,
                    icon: Icons.access_time_rounded,
                    color: AppColors.orange,
                  ),
                ],
              ),
              const SizedBox(height: 22),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(flex: 7, child: teacherOwnAttendancePanel()),
                  const SizedBox(width: 18),
                  Expanded(flex: 5, child: studentAttendancePanel()),
                ],
              ),
            ]
          ],
        ),
      ),
    );
  }

  Widget mobileDashboard() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        topBanner(),
        const SizedBox(height: 18),
        if (isLoading)
          const Padding(
            padding: EdgeInsets.all(30),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (message.isNotEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: UiHelpers.cardDecoration(),
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.red,
                fontWeight: FontWeight.w600,
              ),
            ),
          )
        else ...[
          SizedBox(
            height: 420,
            child: GridView.count(
              crossAxisCount: 2,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.95,
              children: [
                statCard(
                  title: 'TEACHERS',
                  value: teacherTotal,
                  icon: Icons.groups_rounded,
                  color: AppColors.dark,
                ),
                statCard(
                  title: 'PRESENT',
                  value: teacherPresent,
                  icon: Icons.login_rounded,
                  color: AppColors.green,
                  active: true,
                ),
                statCard(
                  title: 'ABSENT',
                  value: teacherAbsent,
                  icon: Icons.sentiment_dissatisfied_rounded,
                  color: AppColors.red,
                ),
                statCard(
                  title: 'LATE',
                  value: teacherLate,
                  icon: Icons.access_time_rounded,
                  color: AppColors.orange,
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          teacherOwnAttendancePanel(),
          const SizedBox(height: 18),
          studentAttendancePanel(),
        ]
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 850;

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(isMobile ? 16 : 24),
          child: isMobile ? mobileDashboard() : desktopDashboard(),
        ),
      ),
    );
  }
}

class AttendancePage extends StatefulWidget {
  const AttendancePage({super.key});

  @override
  State<AttendancePage> createState() => _AttendancePageState();
}

class _AttendancePageState extends State<AttendancePage> {
  final TextEditingController teacherIdController =
      TextEditingController(text: '1');
  final TextEditingController remarksController = TextEditingController();

  XFile? selectedImage;
  Position? currentPosition;

  bool isSubmitting = false;
  String resultMessage = '';

  Future<void> pickSelfie() async {
    final ImagePicker picker = ImagePicker();

    try {
      final XFile? image = await picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 70,
      );

      if (image != null) {
        setState(() {
          selectedImage = image;
        });
      }
    } catch (e) {
      setState(() {
        resultMessage = 'Camera open failed';
      });
    }
  }

  Future<void> fetchLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      setState(() {
        resultMessage = 'Location service is off';
      });
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      setState(() {
        resultMessage = 'Location permission denied';
      });
      return;
    }

    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      setState(() {
        currentPosition = position;
      });
    } catch (e) {
      setState(() {
        resultMessage = 'Failed to get location';
      });
    }
  }

  Future<void> submitAttendance() async {
    if (teacherIdController.text.trim().isEmpty) {
      setState(() {
        resultMessage = 'Teacher ID required';
      });
      return;
    }

    if (currentPosition == null) {
      setState(() {
        resultMessage = 'Get location first';
      });
      return;
    }

    if (selectedImage == null) {
      setState(() {
        resultMessage = 'Take selfie first';
      });
      return;
    }

    setState(() {
      isSubmitting = true;
      resultMessage = '';
    });

    try {
      final uri = Uri.parse('$baseUrl/mobile-api/teacher-attendance/mark/');
      final request = http.MultipartRequest('POST', uri);

      request.headers['Authorization'] = 'Token ${AppSession.token}';
      request.fields['teacher_id'] = teacherIdController.text.trim();
      request.fields['latitude'] = currentPosition!.latitude.toString();
      request.fields['longitude'] = currentPosition!.longitude.toString();
      request.fields['remarks'] = remarksController.text.trim();

      if (selectedImage != null) {
        if (kIsWeb) {
          final bytes = await selectedImage!.readAsBytes();
          request.files.add(
            http.MultipartFile.fromBytes(
              'selfie',
              bytes,
              filename: selectedImage!.name,
            ),
          );
        } else {
          request.files.add(
            await http.MultipartFile.fromPath('selfie', selectedImage!.path),
          );
        }
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      final data = jsonDecode(response.body);

      setState(() {
        if (response.statusCode == 200 && data['status'] == 'success') {
          resultMessage =
              'Success: ${data['message']}\n'
              'Final Status: ${data['final_status']}\n'
              'Distance: ${data['distance_meters']} m\n'
              'Within Range: ${data['within_range']}';
        } else {
          resultMessage = data['message'] ?? 'Attendance failed';
        }
      });
    } catch (e) {
      setState(() {
        resultMessage = 'Server connection error: $e';
      });
    } finally {
      setState(() {
        isSubmitting = false;
      });
    }
  }

  Widget buildInfoBox(String title, String value) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        '$title: $value',
        style: const TextStyle(
          fontWeight: FontWeight.w600,
          color: AppColors.textDark,
        ),
      ),
    );
  }

  Widget actionFilledButton(
    String title,
    IconData icon,
    VoidCallback onTap,
    Color bg,
  ) {
    return SizedBox(
      height: 52,
      child: ElevatedButton.icon(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: bg,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        icon: Icon(icon),
        label: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final latText = currentPosition?.latitude.toString() ?? 'Not fetched';
    final longText = currentPosition?.longitude.toString() ?? 'Not fetched';
    final imageText = selectedImage?.name ?? 'No selfie selected';

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: AppColors.dark,
        foregroundColor: Colors.white,
        title: const Text('Teacher Attendance Panel'),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: UiHelpers.cardDecoration(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  UiHelpers.sectionTitle(
                    'Mark Teacher Attendance',
                    subtitle: 'Selfie + Location based daily attendance',
                  ),
                  const SizedBox(height: 22),
                  TextField(
                    controller: teacherIdController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Teacher ID',
                      prefixIcon: Icon(Icons.badge_outlined),
                    ),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: remarksController,
                    decoration: const InputDecoration(
                      labelText: 'Remarks',
                      prefixIcon: Icon(Icons.edit_note_outlined),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: actionFilledButton(
                          'Take Selfie',
                          Icons.camera_alt_outlined,
                          pickSelfie,
                          AppColors.green,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: actionFilledButton(
                          'Get Location',
                          Icons.my_location_outlined,
                          fetchLocation,
                          AppColors.dark,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    height: 54,
                    child: ElevatedButton.icon(
                      onPressed: isSubmitting ? null : submitAttendance,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.greenDark,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      icon: const Icon(Icons.check_circle_outline),
                      label: Text(
                        isSubmitting ? 'Submitting...' : 'Mark Attendance',
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  buildInfoBox('Latitude', latText),
                  buildInfoBox('Longitude', longText),
                  buildInfoBox('Selfie', imageText),
                  if (resultMessage.isNotEmpty) ...[
                    const SizedBox(height: 18),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.green.withOpacity(0.08),
                        border: Border.all(
                          color: AppColors.green.withOpacity(0.35),
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(
                        resultMessage,
                        style: const TextStyle(
                          color: AppColors.textDark,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ]
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class TeacherReportPage extends StatefulWidget {
  const TeacherReportPage({super.key});

  @override
  State<TeacherReportPage> createState() => _TeacherReportPageState();
}

class _TeacherReportPageState extends State<TeacherReportPage> {
  final TextEditingController employeeIdController =
      TextEditingController(text: '1');

  bool isLoading = false;
  String message = '';
  List<dynamic> records = [];

  Future<void> fetchReport() async {
    if (employeeIdController.text.trim().isEmpty) {
      setState(() {
        message = 'Employee ID required';
      });
      return;
    }

    setState(() {
      isLoading = true;
      message = '';
      records = [];
    });

    try {
      final response = await http.get(
        Uri.parse(
          '$baseUrl/mobile-api/teacher-attendance-report/${employeeIdController.text.trim()}/',
        ),
        headers: {
          'Authorization': 'Token ${AppSession.token}',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        setState(() {
          records = data['results'] ?? [];
        });
      } else {
        setState(() {
          message = data['message'] ?? 'Failed to load report';
        });
      }
    } catch (e) {
      setState(() {
        message = 'Report load error: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Widget reportCard(dynamic item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: UiHelpers.cardDecoration(),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 52,
            width: 52,
            decoration: BoxDecoration(
              color: AppColors.green.withOpacity(0.12),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.event_available_rounded,
              color: AppColors.greenDark,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Date: ${item['date'] ?? ''}',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textDark,
                  ),
                ),
                const SizedBox(height: 8),
                Text('Status: ${item['status'] ?? ''}'),
                Text('Within Range: ${item['within_range'] ?? ''}'),
                Text('Distance: ${item['distance_meters'] ?? ''} m'),
                Text('Remarks: ${item['remarks'] ?? ''}'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: AppColors.dark,
        foregroundColor: Colors.white,
        title: const Text('Teacher Attendance Report'),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 820),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: UiHelpers.cardDecoration(),
                  child: Column(
                    children: [
                      UiHelpers.sectionTitle(
                        'Employee Attendance Report',
                        subtitle: 'Teacher-wise attendance history panel',
                      ),
                      const SizedBox(height: 18),
                      TextField(
                        controller: employeeIdController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Employee ID',
                          prefixIcon: Icon(Icons.badge_outlined),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 52,
                        child: ElevatedButton.icon(
                          onPressed: isLoading ? null : fetchReport,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.dark,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                          icon: const Icon(Icons.search),
                          label: Text(
                            isLoading ? 'Loading...' : 'Load Report',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                        ),
                      ),
                      if (message.isNotEmpty) ...[
                        const SizedBox(height: 14),
                        Text(
                          message,
                          style: const TextStyle(
                            color: AppColors.red,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ]
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                if (records.isNotEmpty)
                  ListView.builder(
                    itemCount: records.length,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemBuilder: (context, index) {
                      return reportCard(records[index]);
                    },
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class StudentAttendancePage extends StatefulWidget {
  const StudentAttendancePage({super.key});

  @override
  State<StudentAttendancePage> createState() =>
      _StudentAttendancePageState();
}

class _StudentAttendancePageState
    extends State<StudentAttendancePage> {

  final List<String> classes = [
    'Nursery',
    'KG',
    'I',
    'II',
    'III',
    'IV',
    'V',
    'VI',
    'VII',
    'VIII',
    'IX',
    'X',
  ];

  String selectedClass = 'VI';

  bool isLoading = false;
  bool isSubmitting = false;

  String message = '';

  List students = [];

  @override
  void initState() {
    super.initState();
    loadStudents();
  }

  Future<void> loadStudents() async {

    setState(() {
      isLoading = true;
      message = '';
    });

    try {

      final response = await http.get(
        Uri.parse(
          '$baseUrl/mobile-api/students-by-class/$selectedClass/',
        ),
        headers: {
          'Authorization': 'Token ${AppSession.token}',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 &&
          data['status'] == 'success') {

        students = data['students'];

        for (var student in students) {
          student['status'] = student['status'] ?? 'Present';
          student['remarks'] = student['remarks'] ?? '';
        }

      } else {

        message = data['message'] ?? 'Failed';

      }

    } catch (e) {

      message = 'Error: $e';

    }

    setState(() {
      isLoading = false;
    });
  }

  Future<void> submitBulkAttendance() async {

    setState(() {
      isSubmitting = true;
      message = '';
    });

    try {

      List attendanceData = [];

      for (var student in students) {

        attendanceData.add({
          'student_id': student['id'],
          'status': student['status'],
          'remarks': '',
        });

      }

      final response = await http.post(
        Uri.parse(
          '$baseUrl/mobile-api/student-attendance/bulk-mark/',
        ),

        headers: {
          'Authorization': 'Token ${AppSession.token}',
          'Content-Type': 'application/json',
        },

        body: jsonEncode({
          'attendance': attendanceData,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 &&
          data['status'] == 'success') {

        message = data['message'];

      } else {

        message = data['message'] ?? 'Failed';

      }

    } catch (e) {

      message = 'Server Error: $e';

    }

    setState(() {
      isSubmitting = false;
    });
  }

  Widget statusButton(
    int index,
    String status,
    Color color,
  ) {

    bool active = students[index]['status'] == status;

    return Expanded(
      child: GestureDetector(
        onTap: () {

          setState(() {
            students[index]['status'] = status;
          });

        },

        child: Container(
          height: 36,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: active
                ? color
                : color.withOpacity(0.12),

            borderRadius: BorderRadius.circular(10),
          ),

          child: Text(
            status,

            style: TextStyle(
              color: active
                  ? Colors.white
                  : color,

              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
      ),
    );
  }

  Widget studentCard(int index) {

    final student = students[index];

    return Container(
      margin: const EdgeInsets.only(bottom: 14),

      padding: const EdgeInsets.all(16),

      decoration: UiHelpers.cardDecoration(),

      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,

        children: [

          Text(
            student['name'] ?? '',

            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
            ),
          ),

          const SizedBox(height: 4),

          Text(
            'Roll: ${student['roll_no']} | ID: ${student['student_id']}',
          ),

          const SizedBox(height: 14),

          Row(
            children: [

              statusButton(
                index,
                'Present',
                AppColors.green,
              ),

              const SizedBox(width: 8),

              statusButton(
                index,
                'Absent',
                AppColors.red,
              ),

              const SizedBox(width: 8),

              statusButton(
                index,
                'Late',
                AppColors.orange,
              ),

            ],
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: AppColors.bg,

      appBar: AppBar(
        backgroundColor: AppColors.dark,
        foregroundColor: Colors.white,

        title: const Text(
          'Bulk Student Attendance',
        ),
      ),

      body: Column(
        children: [

          Padding(
            padding: const EdgeInsets.all(16),

            child: Row(
              children: [

                Expanded(
                  child: DropdownButtonFormField<String>(

                    value: selectedClass,

                    items: classes.map((e) {

                      return DropdownMenuItem(
                        value: e,
                        child: Text(e),
                      );

                    }).toList(),

                    onChanged: (value) {

                      if (value != null) {

                        selectedClass = value;

                        loadStudents();

                      }
                    },

                    decoration: const InputDecoration(
                      labelText: 'Select Class',
                    ),
                  ),
                ),

                const SizedBox(width: 12),

                ElevatedButton(
                  onPressed: loadStudents,

                  child: const Text('Load'),
                )

              ],
            ),
          ),

          Expanded(

            child: isLoading

                ? const Center(
                    child:
                        CircularProgressIndicator(),
                  )

                : ListView.builder(
                    padding:
                        const EdgeInsets.all(16),

                    itemCount: students.length,

                    itemBuilder: (context, index) {

                      return studentCard(index);

                    },
                  ),
          ),

          Container(
            padding: const EdgeInsets.all(16),

            child: Column(
              children: [

                SizedBox(
                  width: double.infinity,
                  height: 54,

                  child: ElevatedButton(

                    onPressed: isSubmitting
                        ? null
                        : submitBulkAttendance,

                    style: ElevatedButton.styleFrom(
                      backgroundColor:
                          AppColors.green,
                      foregroundColor:
                          Colors.white,
                    ),

                    child: Text(
                      isSubmitting
                          ? 'Submitting...'
                          : 'Submit Bulk Attendance',
                    ),
                  ),
                ),

                if (message.isNotEmpty) ...[

                  const SizedBox(height: 10),

                  Text(
                    message,

                    style: const TextStyle(
                      color: AppColors.red,
                      fontWeight:
                          FontWeight.bold,
                    ),
                  ),
                ]
              ],
            ),
          )
        ],
      ),
    );
  }
}

class StudentReportPage extends StatefulWidget {
  const StudentReportPage({super.key});

  @override
  State<StudentReportPage> createState() => _StudentReportPageState();
}

class _StudentReportPageState extends State<StudentReportPage> {
  final List<String> classes = [
    'Nursery', 'KG', 'I', 'II', 'III', 'IV', 'V',
    'VI', 'VII', 'VIII', 'IX', 'X',
  ];

  String selectedClass = 'X';
  String startDate = '2026-05-01';
  String endDate = '2026-05-07';

  bool isLoading = false;
  String message = '';

  List dates = [];
  List rows = [];

  Future<void> fetchRegister() async {
    setState(() {
      isLoading = true;
      message = '';
      dates = [];
      rows = [];
    });

    try {
      final response = await http.get(
        Uri.parse(
          '$baseUrl/mobile-api/student-attendance-register/?class=$selectedClass&start_date=$startDate&end_date=$endDate',
        ),
        headers: {
          'Authorization': 'Token ${AppSession.token}',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        setState(() {
          dates = data['dates'] ?? [];
          rows = data['rows'] ?? [];
        });
      } else {
        setState(() {
          message = data['message'] ?? 'Failed to load attendance register';
        });
      }
    } catch (e) {
      setState(() {
        message = 'Register load error: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Color statusColor(String value) {
    if (value == 'P') return AppColors.greenDark;
    if (value == 'A') return AppColors.red;
    if (value == 'L') return AppColors.orange;
    return AppColors.textLight;
  }

  Widget registerTable() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: WidgetStateProperty.all(AppColors.dark),
        headingTextStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
        ),
        columns: [
          const DataColumn(label: Text('Roll')),
          const DataColumn(label: Text('Name')),
          ...dates.map((d) => DataColumn(label: Text(d['day'].toString()))),
          const DataColumn(label: Text('P')),
          const DataColumn(label: Text('A')),
          const DataColumn(label: Text('L')),
        ],
        rows: rows.map<DataRow>((student) {
          final days = student['days'] ?? [];

          return DataRow(
            cells: [
              DataCell(Text('${student['roll_no'] ?? ''}')),
              DataCell(Text('${student['name'] ?? ''}')),
              ...days.map<DataCell>((d) {
                final s = d['status'].toString();
                return DataCell(
                  Text(
                    s,
                    style: TextStyle(
                      color: statusColor(s),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                );
              }).toList(),
              DataCell(Text('${student['present'] ?? 0}')),
              DataCell(Text('${student['absent'] ?? 0}')),
              DataCell(Text('${student['late'] ?? 0}')),
            ],
          );
        }).toList(),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    fetchRegister();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: AppColors.dark,
        foregroundColor: Colors.white,
        title: const Text('Attendance Register'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(18),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: UiHelpers.cardDecoration(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  UiHelpers.sectionTitle(
                    'Attendance Register',
                    subtitle: 'Class wise date range attendance report',
                  ),
                  const SizedBox(height: 16),

                  DropdownButtonFormField<String>(
                    value: selectedClass,
                    items: classes.map((c) {
                      return DropdownMenuItem(
                        value: c,
                        child: Text(c),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          selectedClass = value;
                        });
                      }
                    },
                    decoration: const InputDecoration(
                      labelText: 'Select Class',
                    ),
                  ),

                  const SizedBox(height: 12),

                  TextField(
                    decoration: const InputDecoration(
                      labelText: 'Start Date',
                      hintText: 'YYYY-MM-DD',
                    ),
                    controller: TextEditingController(text: startDate),
                    onChanged: (v) => startDate = v,
                  ),

                  const SizedBox(height: 12),

                  TextField(
                    decoration: const InputDecoration(
                      labelText: 'End Date',
                      hintText: 'YYYY-MM-DD',
                    ),
                    controller: TextEditingController(text: endDate),
                    onChanged: (v) => endDate = v,
                  ),

                  const SizedBox(height: 16),

                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: isLoading ? null : fetchRegister,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.blue,
                        foregroundColor: Colors.white,
                      ),
                      icon: const Icon(Icons.search),
                      label: Text(isLoading ? 'Loading...' : 'Show Register'),
                    ),
                  ),

                  if (message.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      message,
                      style: const TextStyle(
                        color: AppColors.red,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            const SizedBox(height: 18),

            if (isLoading)
              const Center(child: CircularProgressIndicator())
            else if (rows.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: UiHelpers.cardDecoration(),
                child: registerTable(),
              )
            else
              const Text('No register data found'),
          ],
        ),
      ),
    );
  }
}

class QRStudentAttendancePage extends StatefulWidget {
  const QRStudentAttendancePage({super.key});

  @override
  State<QRStudentAttendancePage> createState() =>
      _QRStudentAttendancePageState();
}

class _QRStudentAttendancePageState extends State<QRStudentAttendancePage> {
  bool isProcessing = false;
  String message = 'Scan student ID card QR code';

  Future<void> markAttendance(String qrData) async {
    if (isProcessing) return;

    setState(() {
      isProcessing = true;
      message = 'Processing QR...';
    });

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/mobile-api/qr-attendance/mark/'),
        headers: {
          'Authorization': 'Token ${AppSession.token}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'qr_data': qrData,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        setState(() {
          message =
              '${data['message']}\n'
              'Name: ${data['student']['name']}\n'
              'Class: ${data['student']['class']}\n'
              'Roll: ${data['student']['roll_no']}\n'
              'Date: ${data['attendance']['date']}\n'
              'Status: ${data['attendance']['status']}';
        });

        if (!mounted) return;

        showDialog(
          context: context,
          builder: (_) => AlertDialog(
            title: const Text('Attendance Success ✅'),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  setState(() {
                    isProcessing = false;
                    message = 'Scan next student QR code';
                  });
                },
                child: const Text('Scan Next'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.pop(context);
                },
                child: const Text('Close'),
              ),
            ],
          ),
        );
      } else {
        setState(() {
          message = data['message'] ?? 'QR attendance failed';
          isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        message = 'Server error: $e';
        isProcessing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: AppColors.dark,
        foregroundColor: Colors.white,
        title: const Text('QR Student Attendance'),
      ),
      body: Column(
        children: [
          Expanded(
            flex: 5,
            child: MobileScanner(
              onDetect: (capture) {
                final barcodes = capture.barcodes;

                if (barcodes.isNotEmpty) {
                  final value = barcodes.first.rawValue;

                  if (value != null && value.isNotEmpty) {
                    markAttendance(value);
                  }
                }
              },
            ),
          ),

          Expanded(
            flex: 2,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                color: Colors.white,
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    isProcessing
                        ? Icons.hourglass_top
                        : Icons.qr_code_scanner,
                    size: 46,
                    color: isProcessing ? AppColors.orange : AppColors.blue,
                  ),
                  const SizedBox(height: 14),
                  Text(
                    message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textDark,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}