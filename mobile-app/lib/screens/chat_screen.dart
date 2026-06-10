import 'package:flutter/material.dart';
import 'package:accounting_platform_mobile/services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ApiService _apiService = ApiService();
  final List<Map<String, dynamic>> _messages = [];
  bool _isLoading = false;

  final List<String> _suggestedPrompts = [
    'What is my GST filing deadline?',
    'How do I calculate input tax credit?',
    'Generate CMA report for my bank loan',
    'Explain Section 115BAC tax regime',
  ];

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _isLoading = true;
      _controller.clear();
    });

    _scrollToBottom();

    try {
      final response = await _apiService.queryAI(
        query: text,
        clientId: '22222222-2222-2222-2222-222222222222',
      );

      setState(() {
        _messages.add({
          'role': 'assistant',
          'content': response['response'] ?? 'No response received',
          'confidence': response['confidence'] ?? 'low',
          'citations': response['citations'] ?? [],
        });
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'assistant',
          'content': 'Sorry, I encountered an error. Please try again.',
          'error': true,
        });
        _isLoading = false;
      });
    }

    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: _messages.isEmpty
              ? _buildSuggestedPrompts()
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final isUser = msg['role'] == 'user';

                    return Align(
                      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.85,
                        ),
                        decoration: BoxDecoration(
                          color: isUser ? Colors.blue[100] : Colors.grey[200],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              msg['content'],
                              style: const TextStyle(fontSize: 14),
                            ),
                            if (!isUser && msg['confidence'] != null) ...[
                              const SizedBox(height: 4),
                              Text(
                                'Confidence: ${msg['confidence']}',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: msg['confidence'] == 'high'
                                      ? Colors.green
                                      : msg['confidence'] == 'medium'
                                          ? Colors.orange
                                          : Colors.red,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        if (_isLoading)
          const Padding(
            padding: EdgeInsets.all(8.0),
            child: LinearProgressIndicator(),
          ),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.grey.withOpacity(0.2),
                blurRadius: 4,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: 'Ask about tax, GST, compliance...',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  onSubmitted: _sendMessage,
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                onPressed: () => _sendMessage(_controller.text),
                icon: const Icon(Icons.send, color: Colors.blue),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSuggestedPrompts() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text(
              'AI Accounting Assistant',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Ask me about tax, GST, compliance, and accounting',
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
            ..._suggestedPrompts.map((prompt) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: OutlinedButton(
                onPressed: () => _sendMessage(prompt),
                child: Text(prompt, textAlign: TextAlign.center),
              ),
            )),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
