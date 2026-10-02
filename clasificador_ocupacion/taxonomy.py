# Authorized vocabulary lists, industry mappings, and English translations

AUTHORIZED_VOCABULARY = [
    'administrativa', 'agricola', 'albañil', 'ama de llaves', 'analista', 
    'ensamblador', 'artista grafico', 'ayudante', 'bartender', 'barista', 
    'carpinteria', 'cajero', 'chofer', 'cocinero', 'conserje', 'construccion', 
    'contable', 'cosmetologia', 'cuidador', 'electricista', 'empleo de verano', 
    'enfermera', 'farmaceutica', 'fast food', 'gerente', 'handyman', 
    'inspector', 'jardinero', 'logistica', 'mantenimiento', 'maestra', 
    'mecanico', 'oficinista', 'operador de maquinaria', 'operario de produccion', 
    'panadero', 'paramedico', 'pintor', 'plomeria', 'quimico', 'recepcionista', 
    'repartidor', 'recursos humanos', 'secretaria', 'servicio al cliente', 
    'tecnico', 'trabajo social', 'vendedor', 'servicios medicos', 'optica', 
    'costura', 'seguridad'
]

INDUSTRY_GROUPS = {
    "salud y cuidado personal": [
        "enfermeros", "enfermera", "asistentes de salud", "asistente de salud",
        "tecnicos de farmacia", "tecnico de farmacia", "paramedicos", "paramedico",
        "dentistas", "dentista", "veterinarios", "veterinario", "servicios medicos",
        "optica", "cuidador"
    ],
    "construccion y produccion": [
        "carpinteros", "carpintero", "carpinteria", "ayudantes de carpinteros",
        "ayudante de carpintero", "pintores", "pintor", "electricistas", "electricista",
        "mecanicos", "mecanico", "operadores", "operador", "operador de maquinaria",
        "operario de produccion", "ensambladores", "ensamblador", "handyman",
        "construccion", "plomeria", "albañil", "costura"
    ],
    "administracion, oficina y tecnologia": [
        "asistentes administrativos", "asistente administrativo", "administrativa",
        "contabilidad", "contable", "recursos humanos", "desarrollador de software",
        "it help desk", "gerentes", "gerente", "analista", "oficinista", "secretaria",
        "recepcionista", "logistica"
    ],
    "servicio al cliente, ventas y hospitalidad": [
        "cajeros", "cajero", "representantes de ventas", "vendedor", "call center",
        "cocineros", "cocinero", "bartender", "barista", "fast food", "panaderos",
        "panadero", "repartidor", "ama de llaves", "empleo de verano"
    ],
    "educacion, seguridad y otros servicios": [
        "maestros", "maestro", "maestra", "trabajadores sociales", "trabajador social",
        "trabajo social", "guardias de seguridad", "guardia de seguridad", "seguridad",
        "conserjes", "conserje", "mantenimiento", "jardinero", "jardineria",
        "agricultura", "agricola", "choferes", "chofer"
    ]
}

# Combine both lists to determine allowed occupations for output mapping
VALID_OCCUPATIONS = list(INDUSTRY_GROUPS.keys()) + AUTHORIZED_VOCABULARY

# Targeted English equivalent optimized for professional job search boards
OCCUPATION_TRANSLATIONS = {
    # Industry groups
    'salud y cuidado personal': 'healthcare and personal care',
    'construccion y produccion': 'construction and production',
    'administracion, oficina y tecnologia': 'administration, office and technology',
    'servicio al cliente, ventas y hospitalidad': 'customer service, sales and hospitality',
    'educacion, seguridad y otros servicios': 'education, security and other services',
    
    # Authorized vocabulary
    'administrativa': 'administrative assistant',
    'agricola': 'agricultural worker',
    'albañil': 'mason',
    'ama de llaves': 'housekeeper',
    'analista': 'analyst',
    'ensamblador': 'assembler',
    'artista grafico': 'graphic designer',
    'ayudante': 'helper',
    'bartender': 'bartender',
    'barista': 'barista',
    'carpinteria': 'carpenter',
    'cajero': 'cashier',
    'chofer': 'driver',
    'cocinero': 'cook',
    'conserje': 'janitor',
    'construccion': 'construction worker',
    'contable': 'accountant',
    'cosmetologia': 'cosmetologist',
    'cuidador': 'caregiver',
    'electricista': 'electrician',
    'empleo de verano': 'summer job',
    'enfermera': 'nurse',
    'farmaceutica': 'pharmaceutical worker',
    'fast food': 'fast food crew member',
    'gerente': 'manager',
    'handyman': 'handyman',
    'inspector': 'inspector',
    'jardinero': 'gardener',
    'logistica': 'logistics specialist',
    'mantenimiento': 'maintenance worker',
    'maestra': 'teacher',
    'mecanico': 'mechanic',
    'oficinista': 'office clerk',
    'operador de maquinaria': 'machinery operator',
    'operario de produccion': 'production worker',
    'panadero': 'baker',
    'paramedico': 'paramedic',
    'pintor': 'painter',
    'plomeria': 'plumber',
    'quimico': 'chemist',
    'recepcionista': 'receptionist',
    'repartidor': 'delivery driver',
    'recursos humanos': 'human resources specialist',
    'secretaria': 'secretary',
    'servicio al cliente': 'customer service representative',
    'tecnico': 'technician',
    'trabajo social': 'social worker',
    'vendedor': 'sales representative',
    'servicios medicos': 'medical services specialist',
    'optica': 'optician',
    'costura': 'seamstress',
    'seguridad': 'security guard'
}
