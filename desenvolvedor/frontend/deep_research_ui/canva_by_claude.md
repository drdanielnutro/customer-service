# Tutorial Avançado: Interface Dinâmica Flutter com Google ADK e Server-Driven UI

Este tutorial aborda a construção de um sistema de renderização dinâmica em Flutter que permite atualizações de interface em tempo real através de JSON estruturado, similar ao sistema de artifacts do Claude, com integração ao Google Agent Development Kit (ADK).

## Parte 1: Fundamentos Arquiteturais (Server-Driven UI + ADK)

### Arquitetura Híbrida: Fixo + Dinâmico

A arquitetura recomendada combina elementos estáticos de UI com áreas de renderização dinâmica, oferecendo o melhor equilíbrio entre performance e flexibilidade.

```dart
// lib/core/architecture/hybrid_screen.dart
class HybridScreen extends StatefulWidget {
  final String screenId;
  
  const HybridScreen({Key? key, required this.screenId}) : super(key: key);
  
  @override
  _HybridScreenState createState() => _HybridScreenState();
}

class _HybridScreenState extends State<HybridScreen> {
  late final ADKService _adkService;
  late final DynamicContentController _contentController;
  
  @override
  void initState() {
    super.initState();
    _adkService = ADKService();
    _contentController = DynamicContentController();
    _loadDynamicContent();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // UI Estática - Sempre presente
      appBar: AppBar(
        title: const Text('Sistema Educacional'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDynamicContent,
          ),
        ],
      ),
      
      // Área Híbrida
      body: Column(
        children: [
          // Seção estática superior
          const StaticHeaderSection(),
          
          // Canvas dinâmico principal
          Expanded(
            child: StreamBuilder<DynamicContent>(
              stream: _contentController.contentStream,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const LoadingCanvas();
                }
                
                return DynamicCanvas(
                  content: snapshot.data!,
                  onInteraction: _handleCanvasInteraction,
                );
              },
            ),
          ),
          
          // Navegação estática inferior
          const BottomNavigationBar(
            items: [...],
          ),
        ],
      ),
    );
  }
  
  Future<void> _loadDynamicContent() async {
    try {
      final response = await _adkService.generateContent(
        prompt: 'Generate educational content for ${widget.screenId}',
        context: _buildContextData(),
      );
      
      _contentController.updateContent(response);
    } catch (e) {
      _handleError(e);
    }
  }
}
```

### Integração com Google ADK

O backend utiliza o Google ADK para gerar conteúdo estruturado através do Gemini:

```python
# backend/adk_service.py
from google.adk.agents import Agent
from google.adk.tools import google_search
import google.generativeai as genai

class FlutterContentAgent:
    def __init__(self):
        self.agent = Agent(
            name="flutter_ui_generator",
            model="gemini-2.0-flash",
            instruction="""You are a Flutter UI generation agent. 
            Generate structured JSON responses for dynamic UI rendering.
            Follow the provided schema strictly.""",
            tools=[google_search]
        )
        
        self.generation_config = {
            "response_mime_type": "application/json",
            "response_schema": self._get_ui_schema()
        }
    
    def _get_ui_schema(self):
        return {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "layout": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["fixed", "dynamic", "hybrid"]},
                        "mainContent": {"$ref": "#/definitions/widget"},
                        "canvas": {
                            "type": "object",
                            "properties": {
                                "visible": {"type": "boolean"},
                                "content": {"$ref": "#/definitions/widget"}
                            }
                        }
                    }
                },
                "widgets": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/widget"}
                }
            },
            "definitions": {
                "widget": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string"},
                        "properties": {"type": "object"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/widget"}
                        },
                        "actions": {"type": "object"}
                    }
                }
            }
        }
    
    async def generate_content(self, prompt: str, context: dict) -> dict:
        enhanced_prompt = self._build_enhanced_prompt(prompt, context)
        
        response = await self.agent.generate_content(
            enhanced_prompt,
            generation_config=self.generation_config
        )
        
        return json.loads(response.text)
```

### Controller de Conteúdo Dinâmico

```dart
// lib/core/controllers/dynamic_content_controller.dart
class DynamicContentController extends ChangeNotifier {
  final _contentStreamController = StreamController<DynamicContent>.broadcast();
  DynamicContent? _currentContent;
  final Map<String, dynamic> _contentState = {};
  
  Stream<DynamicContent> get contentStream => _contentStreamController.stream;
  DynamicContent? get currentContent => _currentContent;
  
  void updateContent(Map<String, dynamic> jsonContent) {
    try {
      _currentContent = DynamicContent.fromJson(jsonContent);
      _contentStreamController.add(_currentContent!);
      notifyListeners();
    } catch (e) {
      _handleParsingError(e, jsonContent);
    }
  }
  
  void updateCanvasState(String key, dynamic value) {
    _contentState[key] = value;
    notifyListeners();
  }
  
  T? getCanvasState<T>(String key) => _contentState[key] as T?;
  
  void clearCanvas() {
    _currentContent = null;
    _contentState.clear();
    _contentStreamController.add(DynamicContent.empty());
    notifyListeners();
  }
  
  @override
  void dispose() {
    _contentStreamController.close();
    super.dispose();
  }
}
```

## Parte 2: Estratégias e Bibliotecas de Renderização

### Análise Comparativa das Principais Bibliotecas

| Biblioteca               | Maturidade | Performance | Complexidade | Recomendação            |
| ------------------------ | ---------- | ----------- | ------------ | ----------------------- |
| **Stac**                 | ★★★★★      | ★★★★☆       | ★★★☆☆        | Produção, SDUI completo |
| **json_dynamic_widget**  | ★★★★★      | ★★★★☆       | ★★★★☆        | Customização avançada   |
| **RFW (Google)**         | ★★★☆☆      | ★★★★★       | ★★★★★        | Projetos Google-first   |
| **Custom WidgetFactory** | ★★★★☆      | ★★★★★       | ★★★☆☆        | Controle total          |

### Implementação com json_dynamic_widget + Customizações

```dart
// lib/rendering/dynamic_widget_renderer.dart
class DynamicWidgetRenderer {
  static final JsonWidgetRegistry _registry = JsonWidgetRegistry.instance;
  
  static void initialize() {
    // Registrar widgets customizados
    _registerCustomWidgets();
    
    // Configurar funções customizadas
    _registerCustomFunctions();
  }
  
  static void _registerCustomWidgets() {
    // Widget de Canvas Educacional
    _registry.registerCustomBuilder(
      'educational_canvas',
      (Map<String, dynamic> map, BuildContext buildContext, 
       JsonWidgetRegistry? registry) {
        return EducationalCanvas(
          config: CanvasConfig.fromJson(map['config']),
          onInteraction: (interaction) {
            final function = registry?.getValue(map['onInteraction']);
            if (function != null) {
              function(interaction);
            }
          },
        );
      },
    );
    
    // Widget de Gráfico Interativo
    _registry.registerCustomBuilder(
      'interactive_chart',
      (Map<String, dynamic> map, BuildContext buildContext, 
       JsonWidgetRegistry? registry) {
        return InteractiveChart(
          data: ChartData.fromJson(map['data']),
          type: ChartType.values.byName(map['type']),
          interactive: map['interactive'] ?? true,
        );
      },
    );
    
    // Widget de Formulário Adaptativo
    _registry.registerCustomBuilder(
      'adaptive_form',
      (Map<String, dynamic> map, BuildContext buildContext, 
       JsonWidgetRegistry? registry) {
        return AdaptiveForm(
          fields: (map['fields'] as List)
              .map((f) => FormField.fromJson(f))
              .toList(),
          onSubmit: (values) {
            final function = registry?.getValue(map['onSubmit']);
            if (function != null) {
              function(values);
            }
          },
        );
      },
    );
  }
  
  static Widget render(Map<String, dynamic> json, BuildContext context) {
    try {
      final widgetData = JsonWidgetData.fromDynamic(json);
      return widgetData.build(context: context);
    } catch (e) {
      return ErrorWidget.withDetails(
        message: 'Erro ao renderizar widget dinâmico',
        error: e,
      );
    }
  }
}
```

### Factory Pattern Customizado para Performance

```dart
// lib/rendering/widget_factory.dart
abstract class DynamicWidgetFactory {
  Widget createWidget(Map<String, dynamic> config, BuildContext context);
  bool canHandle(String type);
}

class OptimizedWidgetFactory implements DynamicWidgetFactory {
  final Map<String, WidgetBuilder> _builders = {};
  final Map<String, Widget> _widgetCache = {};
  
  OptimizedWidgetFactory() {
    _registerCoreBuilders();
  }
  
  void _registerCoreBuilders() {
    // Widgets básicos com cache
    _builders['container'] = (json, context) {
      final cacheKey = _generateCacheKey(json);
      
      return _widgetCache.putIfAbsent(cacheKey, () {
        return Container(
          key: json['key'] != null ? ValueKey(json['key']) : null,
          padding: _parsePadding(json['padding']),
          margin: _parseMargin(json['margin']),
          decoration: _parseDecoration(json['decoration']),
          child: json['child'] != null 
              ? createWidget(json['child'], context)
              : null,
        );
      });
    };
    
    // Widget complexo com otimizações
    _builders['educational_content'] = (json, context) {
      return RepaintBoundary(
        child: EducationalContentWidget(
          content: json['content'],
          interactive: json['interactive'] ?? false,
          onComplete: json['onComplete'],
        ),
      );
    };
  }
  
  @override
  Widget createWidget(Map<String, dynamic> config, BuildContext context) {
    final type = config['type'] as String;
    final builder = _builders[type];
    
    if (builder == null) {
      return _createFallbackWidget(type, config);
    }
    
    return builder(config, context);
  }
  
  @override
  bool canHandle(String type) => _builders.containsKey(type);
  
  String _generateCacheKey(Map<String, dynamic> json) {
    // Gera chave única baseada no conteúdo
    return '${json['type']}_${json.hashCode}';
  }
}
```

## Parte 3: Tutorial Prático com Código Completo

### Estrutura do Projeto

```
flutter_dynamic_ui/
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── models/
│   │   │   ├── dynamic_content.dart
│   │   │   ├── widget_config.dart
│   │   │   └── canvas_state.dart
│   │   ├── services/
│   │   │   ├── adk_service.dart
│   │   │   └── cache_service.dart
│   │   ├── controllers/
│   │   │   └── dynamic_content_controller.dart
│   │   └── utils/
│   │       └── json_validators.dart
│   ├── presentation/
│   │   ├── screens/
│   │   │   └── hybrid_screen.dart
│   │   ├── widgets/
│   │   │   ├── dynamic_canvas.dart
│   │   │   ├── educational_widgets/
│   │   │   └── common/
│   │   └── renderers/
│   │       ├── widget_renderer.dart
│   │       └── canvas_renderer.dart
│   └── features/
│       └── educational/
│           ├── models/
│           ├── widgets/
│           └── controllers/
├── pubspec.yaml
└── README.md
```

### Implementação Completa do Sistema

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar serviços
  await initializeServices();
  
  runApp(
    ProviderScope(
      child: DynamicUIApp(),
    ),
  );
}

Future<void> initializeServices() async {
  // Inicializar renderizadores
  DynamicWidgetRenderer.initialize();
  
  // Configurar cache
  await CacheService.initialize();
  
  // Configurar ADK
  ADKService.configure(
    baseUrl: const String.fromEnvironment('ADK_BASE_URL'),
    apiKey: const String.fromEnvironment('ADK_API_KEY'),
  );
}

class DynamicUIApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dynamic UI Educational System',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HybridScreen(screenId: 'main'),
    );
  }
}
```

```dart
// lib/core/models/dynamic_content.dart
class DynamicContent {
  final String version;
  final Layout layout;
  final Canvas? canvas;
  final Map<String, dynamic> metadata;
  
  const DynamicContent({
    required this.version,
    required this.layout,
    this.canvas,
    this.metadata = const {},
  });
  
  factory DynamicContent.fromJson(Map<String, dynamic> json) {
    return DynamicContent(
      version: json['version'] ?? '1.0',
      layout: Layout.fromJson(json['layout']),
      canvas: json['canvas'] != null 
          ? Canvas.fromJson(json['canvas'])
          : null,
      metadata: json['metadata'] ?? {},
    );
  }
  
  static DynamicContent empty() => DynamicContent(
    version: '1.0',
    layout: Layout.empty(),
  );
}

class Canvas {
  final bool visible;
  final WidgetConfig content;
  final CanvasInteractionMode interactionMode;
  final Map<String, dynamic> state;
  
  const Canvas({
    required this.visible,
    required this.content,
    this.interactionMode = CanvasInteractionMode.interactive,
    this.state = const {},
  });
  
  factory Canvas.fromJson(Map<String, dynamic> json) {
    return Canvas(
      visible: json['visible'] ?? true,
      content: WidgetConfig.fromJson(json['content']),
      interactionMode: CanvasInteractionMode.values.byName(
        json['interactionMode'] ?? 'interactive'
      ),
      state: json['state'] ?? {},
    );
  }
}

enum CanvasInteractionMode {
  readonly,
  interactive,
  editable,
}
```

```dart
// lib/presentation/widgets/dynamic_canvas.dart
class DynamicCanvas extends StatefulWidget {
  final DynamicContent content;
  final Function(CanvasInteraction) onInteraction;
  
  const DynamicCanvas({
    Key? key,
    required this.content,
    required this.onInteraction,
  }) : super(key: key);
  
  @override
  _DynamicCanvasState createState() => _DynamicCanvasState();
}

class _DynamicCanvasState extends State<DynamicCanvas> 
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  final Map<String, dynamic> _localState = {};
  
  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _animationController.forward();
  }
  
  @override
  Widget build(BuildContext context) {
    if (widget.content.canvas == null || !widget.content.canvas!.visible) {
      return const SizedBox.shrink();
    }
    
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: _animationController,
        builder: (context, child) {
          return FadeTransition(
            opacity: _animationController,
            child: Container(
              margin: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: _buildCanvasContent(),
            ),
          );
        },
      ),
    );
  }
  
  Widget _buildCanvasContent() {
    final canvas = widget.content.canvas!;
    
    return GestureDetector(
      onTap: canvas.interactionMode == CanvasInteractionMode.interactive
          ? () => _handleTap(canvas)
          : null,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: CustomPaint(
          painter: canvas.content.type == 'custom_graphics'
              ? GraphicsCanvasPainter(canvas.content)
              : null,
          child: _renderWidgetContent(canvas.content),
        ),
      ),
    );
  }
  
  Widget _renderWidgetContent(WidgetConfig config) {
    try {
      return DynamicWidgetRenderer.render(
        config.toJson(),
        context,
      );
    } catch (e) {
      return _buildErrorWidget(e);
    }
  }
  
  void _handleTap(Canvas canvas) {
    widget.onInteraction(
      CanvasInteraction(
        type: InteractionType.tap,
        timestamp: DateTime.now(),
        data: {'canvasState': _localState},
      ),
    );
  }
  
  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
}
```

### Serviço ADK com Flutter

```dart
// lib/core/services/adk_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ADKService {
  static late String _baseUrl;
  static late String _apiKey;
  
  static void configure({
    required String baseUrl,
    required String apiKey,
  }) {
    _baseUrl = baseUrl;
    _apiKey = apiKey;
  }
  
  Future<Map<String, dynamic>> generateContent({
    required String prompt,
    Map<String, dynamic>? context,
    UIGenerationConfig? config,
  }) async {
    final request = UIGenerationRequest(
      prompt: prompt,
      context: context ?? {},
      config: config ?? UIGenerationConfig.defaultConfig(),
    );
    
    try {
      final response = await _makeRequest(
        endpoint: '/generate-ui',
        body: request.toJson(),
      );
      
      return _validateAndParseResponse(response);
    } on ADKException {
      rethrow;
    } catch (e) {
      throw ADKException('Unexpected error: $e');
    }
  }
  
  Future<Map<String, dynamic>> refineContent({
    required String refinementPrompt,
    required Map<String, dynamic> currentContent,
  }) async {
    final request = {
      'refinement_prompt': refinementPrompt,
      'current_content': currentContent,
      'preserve_state': true,
    };
    
    final response = await _makeRequest(
      endpoint: '/refine-ui',
      body: request,
    );
    
    return _validateAndParseResponse(response);
  }
  
  Future<http.Response> _makeRequest({
    required String endpoint,
    required Map<String, dynamic> body,
  }) async {
    final uri = Uri.parse('$_baseUrl$endpoint');
    
    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_apiKey',
        'X-Client-Version': '1.0.0',
      },
      body: jsonEncode(body),
    ).timeout(
      const Duration(seconds: 30),
      onTimeout: () => throw ADKException('Request timeout'),
    );
    
    return response;
  }
  
  Map<String, dynamic> _validateAndParseResponse(http.Response response) {
    switch (response.statusCode) {
      case 200:
      case 201:
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          
          // Validar estrutura básica
          if (!data.containsKey('version') || !data.containsKey('layout')) {
            throw ADKException('Invalid response structure');
          }
          
          return data;
        } on FormatException {
          throw ADKException('Invalid JSON response');
        }
      
      case 400:
        throw ADKException('Bad request: ${_extractError(response)}');
      
      case 401:
        throw ADKException('Unauthorized: Check API key');
      
      case 429:
        throw ADKException('Rate limit exceeded');
      
      case 500:
      case 502:
      case 503:
        throw ADKException('Server error: ${response.statusCode}');
      
      default:
        throw ADKException('HTTP ${response.statusCode}: ${response.reasonPhrase}');
    }
  }
  
  String _extractError(http.Response response) {
    try {
      final error = jsonDecode(response.body);
      return error['message'] ?? error['error'] ?? 'Unknown error';
    } catch (_) {
      return response.body;
    }
  }
}

class UIGenerationRequest {
  final String prompt;
  final Map<String, dynamic> context;
  final UIGenerationConfig config;
  
  UIGenerationRequest({
    required this.prompt,
    required this.context,
    required this.config,
  });
  
  Map<String, dynamic> toJson() => {
    'prompt': prompt,
    'context': context,
    'config': config.toJson(),
    'response_schema': _getResponseSchema(),
  };
  
  Map<String, dynamic> _getResponseSchema() => {
    'type': 'object',
    'properties': {
      'version': {'type': 'string'},
      'layout': {
        'type': 'object',
        'properties': {
          'type': {'type': 'string'},
          'mainContent': {'type': 'object'},
        },
      },
      'canvas': {
        'type': 'object',
        'properties': {
          'visible': {'type': 'boolean'},
          'content': {'type': 'object'},
        },
      },
    },
    'required': ['version', 'layout'],
  };
}
```

## Parte 4: Contrato JSON Completo com Exemplos

### Schema JSON Principal

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DynamicUISchema",
  "type": "object",
  "required": ["version", "layout"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "author": {"type": "string"},
        "created": {"type": "string", "format": "date-time"},
        "tags": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "theme": {
      "type": "object",
      "properties": {
        "primaryColor": {"type": "string", "format": "color"},
        "backgroundColor": {"type": "string", "format": "color"},
        "fontFamily": {"type": "string"},
        "spacing": {
          "type": "object",
          "properties": {
            "small": {"type": "number"},
            "medium": {"type": "number"},
            "large": {"type": "number"}
          }
        }
      }
    },
    "layout": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["fixed", "dynamic", "hybrid"]
        },
        "mainContent": {"$ref": "#/definitions/widget"},
        "areas": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "type": {"type": "string"},
              "content": {"$ref": "#/definitions/widget"}
            }
          }
        }
      }
    },
    "canvas": {
      "type": "object",
      "properties": {
        "visible": {"type": "boolean"},
        "interactionMode": {
          "type": "string",
          "enum": ["readonly", "interactive", "editable"]
        },
        "content": {"$ref": "#/definitions/widget"},
        "state": {"type": "object"}
      }
    },
    "actions": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/action"
      }
    }
  },
  "definitions": {
    "widget": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "id": {"type": "string"},
        "type": {"type": "string"},
        "properties": {"type": "object"},
        "children": {
          "type": "array",
          "items": {"$ref": "#/definitions/widget"}
        },
        "actions": {
          "type": "object",
          "additionalProperties": {"$ref": "#/definitions/action"}
        }
      }
    },
    "action": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["navigate", "update_state", "api_call", "show_dialog"]
        },
        "params": {"type": "object"}
      }
    }
  }
}
```

### Exemplos de Respostas JSON

#### Exemplo 1: Quiz Interativo

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Quiz de Matemática",
    "description": "Teste seus conhecimentos em álgebra",
    "tags": ["educação", "matemática", "quiz"]
  },
  "layout": {
    "type": "hybrid",
    "mainContent": {
      "type": "column",
      "properties": {
        "padding": 16,
        "crossAxisAlignment": "stretch"
      },
      "children": [
        {
          "type": "text",
          "properties": {
            "text": "Questão 1 de 5",
            "style": {
              "fontSize": 14,
              "color": "#666666"
            }
          }
        },
        {
          "type": "progress_indicator",
          "properties": {
            "value": 0.2,
            "color": "#2196F3"
          }
        }
      ]
    }
  },
  "canvas": {
    "visible": true,
    "interactionMode": "interactive",
    "content": {
      "type": "quiz_widget",
      "properties": {
        "question": "Qual é o valor de x em: 2x + 5 = 15?",
        "options": [
          {"id": "a", "text": "x = 5", "value": 5},
          {"id": "b", "text": "x = 10", "value": 10},
          {"id": "c", "text": "x = 7.5", "value": 7.5},
          {"id": "d", "text": "x = 3", "value": 3}
        ],
        "correctAnswer": "a",
        "explanation": "Resolvendo: 2x + 5 = 15 → 2x = 10 → x = 5"
      },
      "actions": {
        "onAnswer": {
          "type": "update_state",
          "params": {
            "key": "currentQuestion",
            "increment": 1
          }
        }
      }
    },
    "state": {
      "currentQuestion": 1,
      "totalQuestions": 5,
      "score": 0
    }
  }
}
```

#### Exemplo 2: Apresentação Multi-Step

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Introdução à Física Quântica",
    "description": "Conceitos fundamentais explicados passo a passo"
  },
  "layout": {
    "type": "dynamic"
  },
  "canvas": {
    "visible": true,
    "interactionMode": "interactive",
    "content": {
      "type": "carousel",
      "properties": {
        "autoPlay": false,
        "showIndicators": true,
        "enableGestures": true
      },
      "children": [
        {
          "type": "slide",
          "properties": {
            "background": "#1a237e",
            "padding": 32
          },
          "children": [
            {
              "type": "animated_text",
              "properties": {
                "text": "O Mundo Quântico",
                "animation": "fadeIn",
                "style": {
                  "fontSize": 32,
                  "fontWeight": "bold",
                  "color": "white"
                }
              }
            },
            {
              "type": "lottie_animation",
              "properties": {
                "asset": "assets/animations/quantum_particles.json",
                "autoPlay": true,
                "loop": true
              }
            }
          ]
        },
        {
          "type": "slide",
          "properties": {
            "background": "white",
            "padding": 24
          },
          "children": [
            {
              "type": "interactive_diagram",
              "properties": {
                "type": "double_slit_experiment",
                "interactive": true,
                "showLabels": true
              }
            },
            {
              "type": "expandable_text",
              "properties": {
                "title": "Experimento da Dupla Fenda",
                "content": "Demonstra a dualidade onda-partícula...",
                "maxLines": 3
              }
            }
          ]
        }
      ]
    }
  }
}
```

#### Exemplo 3: Formulário Adaptativo

```json
{
  "version": "1.0",
  "layout": {
    "type": "hybrid"
  },
  "canvas": {
    "visible": true,
    "interactionMode": "editable",
    "content": {
      "type": "adaptive_form",
      "properties": {
        "id": "student_assessment",
        "title": "Avaliação do Estudante"
      },
      "children": [
        {
          "type": "form_field",
          "properties": {
            "name": "difficulty_level",
            "label": "Qual seu nível de conhecimento?",
            "fieldType": "dropdown",
            "options": [
              {"value": "beginner", "label": "Iniciante"},
              {"value": "intermediate", "label": "Intermediário"},
              {"value": "advanced", "label": "Avançado"}
            ],
            "required": true
          },
          "actions": {
            "onChange": {
              "type": "update_state",
              "params": {
                "key": "adaptiveFields",
                "condition": "value === 'advanced'",
                "showFields": ["advanced_topics", "research_interest"]
              }
            }
          }
        },
        {
          "type": "form_field",
          "properties": {
            "name": "learning_goals",
            "label": "Quais são seus objetivos?",
            "fieldType": "multiselect",
            "options": [
              {"value": "theory", "label": "Compreender teoria"},
              {"value": "practice", "label": "Prática e exercícios"},
              {"value": "projects", "label": "Projetos reais"}
            ]
          }
        },
        {
          "type": "conditional_group",
          "properties": {
            "condition": "difficulty_level === 'advanced'",
            "visible": false
          },
          "children": [
            {
              "type": "form_field",
              "properties": {
                "name": "advanced_topics",
                "label": "Tópicos avançados de interesse",
                "fieldType": "chips",
                "options": ["Machine Learning", "Quantum Computing", "Blockchain"]
              }
            }
          ]
        }
      ],
      "actions": {
        "onSubmit": {
          "type": "api_call",
          "params": {
            "endpoint": "/api/assessment/submit",
            "method": "POST"
          }
        }
      }
    }
  }
}
```

## Parte 5: Casos de Uso Educacionais

### Sistema de Exercícios Adaptativos

```dart
// lib/features/educational/adaptive_exercises.dart
class AdaptiveExerciseSystem extends StatefulWidget {
  final String topicId;
  final UserProfile userProfile;
  
  const AdaptiveExerciseSystem({
    Key? key,
    required this.topicId,
    required this.userProfile,
  }) : super(key: key);
  
  @override
  _AdaptiveExerciseSystemState createState() => _AdaptiveExerciseSystemState();
}

class _AdaptiveExerciseSystemState extends State<AdaptiveExerciseSystem> {
  late final AdaptiveEngine _adaptiveEngine;
  late final ExerciseController _exerciseController;
  
  @override
  void initState() {
    super.initState();
    _adaptiveEngine = AdaptiveEngine(
      userProfile: widget.userProfile,
      topicId: widget.topicId,
    );
    _exerciseController = ExerciseController();
    _loadNextExercise();
  }
  
  Future<void> _loadNextExercise() async {
    final difficulty = _adaptiveEngine.calculateNextDifficulty();
    
    final exerciseJson = await ADKService().generateContent(
      prompt: '''
        Generate an educational exercise for topic: ${widget.topicId}
        Difficulty level: $difficulty
        User performance: ${_adaptiveEngine.getPerformanceMetrics()}
        Format: Interactive exercise with immediate feedback
      ''',
      config: UIGenerationConfig(
        widgetTypes: ['quiz', 'drag_drop', 'fill_blanks', 'matching'],
        includeExplanations: true,
        adaptiveDifficulty: true,
      ),
    );
    
    _exerciseController.loadExercise(exerciseJson);
  }
  
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Exercise?>(
      stream: _exerciseController.currentExercise,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const LoadingIndicator();
        }
        
        return Column(
          children: [
            PerformanceHeader(
              metrics: _adaptiveEngine.getPerformanceMetrics(),
            ),
            Expanded(
              child: DynamicCanvas(
                content: snapshot.data!.content,
                onInteraction: _handleExerciseInteraction,
              ),
            ),
            AdaptiveHintSystem(
              exercise: snapshot.data!,
              onHintRequest: _provideAdaptiveHint,
            ),
          ],
        );
      },
    );
  }
  
  void _handleExerciseInteraction(CanvasInteraction interaction) {
    final result = _exerciseController.processAnswer(interaction.data);
    
    _adaptiveEngine.recordPerformance(
      exerciseId: _exerciseController.currentExerciseId!,
      result: result,
      timeSpent: interaction.timestamp.difference(_exerciseStartTime),
    );
    
    if (result.isCorrect) {
      _showFeedback(result.feedback, positive: true);
      Future.delayed(const Duration(seconds: 2), _loadNextExercise);
    } else {
      _showFeedback(result.feedback, positive: false);
      _offerHint();
    }
  }
}
```

### Questionário Gamificado

```dart
// lib/features/educational/gamified_quiz.dart
class GamifiedQuizWidget extends StatefulWidget {
  final QuizConfig config;
  
  const GamifiedQuizWidget({Key? key, required this.config}) : super(key: key);
  
  @override
  _GamifiedQuizWidgetState createState() => _GamifiedQuizWidgetState();
}

class _GamifiedQuizWidgetState extends State<GamifiedQuizWidget> 
    with TickerProviderStateMixin {
  late final AnimationController _scoreAnimationController;
  late final AnimationController _progressAnimationController;
  final GamificationEngine _gamificationEngine = GamificationEngine();
  
  int _currentScore = 0;
  int _streak = 0;
  double _multiplier = 1.0;
  
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Background com efeitos visuais
        AnimatedBackground(
          animation: _progressAnimationController,
          gradient: _getAdaptiveGradient(),
        ),
        
        // Conteúdo principal
        SafeArea(
          child: Column(
            children: [
              // Header gamificado
              GamifiedHeader(
                score: _currentScore,
                streak: _streak,
                multiplier: _multiplier,
                level: _gamificationEngine.currentLevel,
                experience: _gamificationEngine.experience,
              ),
              
              // Quiz content
              Expanded(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 500),
                  transitionBuilder: (child, animation) {
                    return FadeTransition(
                      opacity: animation,
                      child: SlideTransition(
                        position: animation.drive(
                          Tween(
                            begin: const Offset(0.1, 0),
                            end: Offset.zero,
                          ),
                        ),
                        child: child,
                      ),
                    );
                  },
                  child: _buildCurrentQuestion(),
                ),
              ),
              
              // Power-ups e helpers
              PowerUpBar(
                availablePowerUps: _gamificationEngine.powerUps,
                onUsePowerUp: _handlePowerUp,
              ),
            ],
          ),
        ),
        
        // Overlay de conquistas
        AchievementOverlay(
          achievementStream: _gamificationEngine.achievementStream,
        ),
      ],
    );
  }
  
  Widget _buildCurrentQuestion() {
    return DynamicCanvas(
      key: ValueKey(widget.config.currentQuestionId),
      content: widget.config.currentQuestion,
      onInteraction: (interaction) {
        final isCorrect = _evaluateAnswer(interaction);
        
        if (isCorrect) {
          _streak++;
          _multiplier = min(_multiplier + 0.1, 3.0);
          _currentScore += (100 * _multiplier).round();
          
          _gamificationEngine.recordCorrectAnswer(
            questionId: widget.config.currentQuestionId,
            score: _currentScore,
            streak: _streak,
          );
          
          _triggerSuccessAnimation();
        } else {
          _streak = 0;
          _multiplier = 1.0;
          _triggerFailureAnimation();
        }
        
        _moveToNextQuestion();
      },
    );
  }
}
```

### Visualização de Progresso Educacional

```dart
// lib/features/educational/progress_visualization.dart
class EducationalProgressDashboard extends StatelessWidget {
  final String studentId;
  
  const EducationalProgressDashboard({
    Key? key,
    required this.studentId,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ProgressData>(
      future: _loadProgressData(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const LoadingIndicator();
        }
        
        return SingleChildScrollView(
          child: Column(
            children: [
              // Gráfico de progresso geral
              ProgressChart(
                data: snapshot.data!.overallProgress,
                type: ChartType.radialProgress,
              ),
              
              // Mapa de calor de atividades
              ActivityHeatmap(
                activities: snapshot.data!.dailyActivities,
                onDayTap: _showDayDetails,
              ),
              
              // Conquistas e badges
              AchievementGrid(
                achievements: snapshot.data!.achievements,
                unlockedCount: snapshot.data!.unlockedAchievements,
              ),
              
              // Análise de performance por tópico
              TopicPerformanceBreakdown(
                topics: snapshot.data!.topicPerformance,
                renderMode: RenderMode.interactive,
              ),
              
              // Recomendações personalizadas
              AdaptiveRecommendations(
                studentProfile: snapshot.data!.profile,
                onRecommendationTap: _navigateToContent,
              ),
            ],
          ),
        );
      },
    );
  }
  
  Future<ProgressData> _loadProgressData() async {
    final response = await ADKService().generateContent(
      prompt: '''
        Generate a comprehensive progress dashboard for student: $studentId
        Include: overall progress, daily activities, achievements, topic performance
        Format: Interactive visualizations with drill-down capabilities
      ''',
      config: UIGenerationConfig(
        widgetTypes: ['chart', 'heatmap', 'grid', 'progress_bar'],
        includeInteractivity: true,
      ),
    );
    
    return ProgressData.fromJson(response);
  }
}
```

### Sistema de Apresentações Interativas

```dart
// lib/features/educational/interactive_presentations.dart
class InteractivePresentationSystem extends StatefulWidget {
  final String presentationId;
  
  const InteractivePresentationSystem({
    Key? key,
    required this.presentationId,
  }) : super(key: key);
  
  @override
  _InteractivePresentationSystemState createState() => 
      _InteractivePresentationSystemState();
}

class _InteractivePresentationSystemState 
    extends State<InteractivePresentationSystem> {
  late final PresentationController _controller;
  final InteractionRecorder _interactionRecorder = InteractionRecorder();
  
  @override
  void initState() {
    super.initState();
    _controller = PresentationController(
      presentationId: widget.presentationId,
      onSlideChange: _handleSlideChange,
    );
    _loadPresentation();
  }
  
  Future<void> _loadPresentation() async {
    final presentationJson = await ADKService().generateContent(
      prompt: '''
        Load interactive presentation: ${widget.presentationId}
        Include: animations, interactive elements, embedded quizzes
        Support: touch gestures, voice narration, real-time annotations
      ''',
      config: UIGenerationConfig(
        widgetTypes: [
          'slide', 
          'animation', 
          'interactive_diagram',
          'embedded_quiz',
          'video_player',
          '3d_model'
        ],
        enableGestures: true,
        includeNarration: true,
      ),
    );
    
    _controller.loadPresentation(presentationJson);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Apresentação principal
          GestureDetector(
            onTap: () => _controller.nextSlide(),
            onDoubleTap: () => _controller.previousSlide(),
            onLongPress: _showInteractiveMenu,
            child: StreamBuilder<PresentationSlide>(
              stream: _controller.currentSlide,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const LoadingSlide();
                }
                
                return AnimatedSlideTransition(
                  slide: snapshot.data!,
                  animation: _controller.slideAnimation,
                  onInteraction: _handleSlideInteraction,
                );
              },
            ),
          ),
          
          // Controles de navegação
          Positioned(
            bottom: 20,
            left: 0,
            right: 0,
            child: PresentationControls(
              controller: _controller,
              totalSlides: _controller.totalSlides,
              currentSlide: _controller.currentSlideIndex,
              onNavigate: _navigateToSlide,
            ),
          ),
          
          // Indicador de interações
          Positioned(
            top: 20,
            right: 20,
            child: InteractionIndicator(
              interactionCount: _interactionRecorder.count,
              onTap: _showInteractionHistory,
            ),
          ),
          
          // Anotações ao vivo
          if (_controller.annotationsEnabled)
            AnnotationLayer(
              onAnnotation: _saveAnnotation,
              currentSlideId: _controller.currentSlideId,
            ),
        ],
      ),
    );
  }
  
  void _handleSlideInteraction(SlideInteraction interaction) {
    _interactionRecorder.record(interaction);
    
    switch (interaction.type) {
      case InteractionType.quiz:
        _showEmbeddedQuiz(interaction.data);
        break;
      case InteractionType.video:
        _playVideo(interaction.data);
        break;
      case InteractionType.interactive3D:
        _launch3DViewer(interaction.data);
        break;
      case InteractionType.diagram:
        _showInteractiveDiagram(interaction.data);
        break;
    }
  }
}
```

## Considerações de Performance e Otimização

### Estratégias de Cache

```dart
// lib/core/services/cache_service.dart
class CacheService {
  static final _memoryCache = <String, CachedContent>{};
  static late Box<String> _persistentCache;
  
  static Future<void> initialize() async {
    await Hive.initFlutter();
    _persistentCache = await Hive.openBox<String>('ui_cache');
  }
  
  static Future<Map<String, dynamic>?> getCachedContent(String key) async {
    // Verificar cache em memória
    if (_memoryCache.containsKey(key)) {
      final cached = _memoryCache[key]!;
      if (!cached.isExpired) {
        return cached.content;
      }
      _memoryCache.remove(key);
    }
    
    // Verificar cache persistente
    final persistentData = _persistentCache.get(key);
    if (persistentData != null) {
      try {
        final content = jsonDecode(persistentData) as Map<String, dynamic>;
        final cachedAt = DateTime.parse(content['_cachedAt']);
        
        if (DateTime.now().difference(cachedAt) < const Duration(hours: 24)) {
          // Promover para cache em memória
          _memoryCache[key] = CachedContent(
            content: content,
            cachedAt: cachedAt,
          );
          return content;
        }
      } catch (_) {
        _persistentCache.delete(key);
      }
    }
    
    return null;
  }
  
  static Future<void> cacheContent(
    String key, 
    Map<String, dynamic> content,
  ) async {
    content['_cachedAt'] = DateTime.now().toIso8601String();
    
    // Cache em memória
    _memoryCache[key] = CachedContent(
      content: content,
      cachedAt: DateTime.now(),
    );
    
    // Cache persistente
    await _persistentCache.put(key, jsonEncode(content));
  }
}
```

### Otimização de Renderização

```dart
// lib/core/optimizations/render_optimizer.dart
class RenderOptimizer {
  static Widget optimizeWidget(Widget widget, {
    bool enableRepaintBoundary = true,
    bool enableKeepAlive = false,
  }) {
    Widget optimized = widget;
    
    if (enableRepaintBoundary) {
      optimized = RepaintBoundary(child: optimized);
    }
    
    if (enableKeepAlive) {
      optimized = KeepAliveWrapper(child: optimized);
    }
    
    return optimized;
  }
}

class KeepAliveWrapper extends StatefulWidget {
  final Widget child;
  
  const KeepAliveWrapper({Key? key, required this.child}) : super(key: key);
  
  @override
  _KeepAliveWrapperState createState() => _KeepAliveWrapperState();
}

class _KeepAliveWrapperState extends State<KeepAliveWrapper> 
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  
  @override
  Widget build(BuildContext context) {
    super.build(context);
    return widget.child;
  }
}
```

## Conclusão

Este tutorial apresentou uma arquitetura completa para construção de interfaces dinâmicas em Flutter com integração ao Google ADK. A solução oferece:

1. **Flexibilidade**: Suporte para múltiplos tipos de conteúdo educacional
2. **Performance**: Otimizações de cache e renderização
3. **Escalabilidade**: Arquitetura modular e extensível
4. **Manutenibilidade**: Separação clara entre UI estática e dinâmica
5. **Experiência do Usuário**: Animações fluidas e interações intuitivas

O sistema permite atualizações de conteúdo em tempo real sem necessidade de atualizar o aplicativo, similar ao sistema de artifacts do Claude, mas adaptado para contextos educacionais com recursos avançados de gamificação, adaptatividade e visualização de progresso.