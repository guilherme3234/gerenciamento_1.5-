from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from .forms import FormLogin, formCadastroUsuario, InventarioForm, SalaForm
from .models import Senai
from django.contrib.auth.models import User, Group
from .models import Inventario, Sala
from django.core.cache import cache
from django.http import HttpResponse
from .models import Inventario
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout

# Create your views here.

def homepage(request):
    # Se o usuário já estiver autenticado, redirecione para outra página
    if request.user.is_authenticated:
        return redirect('welcomeHomepage')  # Substitua pelo nome da página desejada
    return render(request, 'homepage.html')

def login(request):
    return render(request, 'login.html')


def profile(request):
    return render(request, 'profile.html')

def faq(request):
    return render(request, 'faq.html')

from django.contrib.auth.models import Group


#logouut 
def logout(request):
    auth_logout(request)
    return redirect('login')

def filtrar_inventario_por_grupo(user, is_coordenador, is_professor):
    """
    Filtra o inventário com base no grupo do usuário.
    - Coordenador vê todos os itens.
    - Professor vê apenas os itens das salas que ele gerencia.
    - Outros usuários não veem nada.
    """
    if is_coordenador:
        return Inventario.objects.all()  # Coordenador vê todos os itens
    elif is_professor:
        salas_responsavel = Sala.objects.filter(responsavel=user.username).values_list('sala', flat=True)
        return Inventario.objects.filter(sala__in=salas_responsavel)  # Professor vê itens de suas salas
    return Inventario.objects.none()  # Usuário sem permissão não vê nada


def aplicar_filtros_inventario(inventario, query, ordem, sala):
    """
    Aplica filtros de pesquisa, ordenação e sala ao inventário.
    """
    if query:
        inventario = inventario.filter(num_inventario__icontains=query)
    if ordem:
        inventario = inventario.order_by('denominacao' if ordem == 'A-Z' else '-denominacao')
    if sala:
        inventario = inventario.filter(sala__icontains=sala)
    return inventario

def aplicar_filtros_salas(salas, query, ordem):
    """
    Aplica os filtros de pesquisa e ordenação às salas.
    """
    if query:
        salas = salas.filter(sala__icontains=query)
    if ordem:
        salas = salas.order_by('sala' if ordem == 'A-Z' else '-sala')
    return salas

def verificar_grupo_usuario(user):
    """
    Verifica se o usuário pertence aos grupos 'Coordenador' ou 'Professor'.
    """
    is_coordenador = user.groups.filter(name="Coordenador").exists()
    is_professor = user.groups.filter(name="Professor").exists()
    return is_coordenador, is_professor

def filtrar_salas(user, is_coordenador, is_professor):
    """
    Filtra as salas com base no grupo do usuário.
    """
    if is_coordenador:
        return Sala.objects.all()  # Coordenador vê todas as salas
    elif is_professor:
        return Sala.objects.filter(responsavel=user.username)  # Professor vê salas específicas
    return []  # Usuário sem grupo relevante não vê nada



@login_required
def welcomeHomepage(request):
    """
    View principal para a página de boas-vindas.
    """
    # Verifica os grupos do usuário
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Filtra as salas com base nos grupos
    sala = filtrar_salas(request.user, is_coordenador, is_professor)

    # Processa o formulário
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('welcomeHomepage')
    else:
        form = SalaForm()


    # Renderiza a página com o contexto adequado
    return render(request, 'welcomeHomepage.html', {
        'form': form,
        'sala': sala,
        'is_coordenador': is_coordenador,
        'is_professor': is_professor,
    })




# Importar o modelo de itens (substitua Item pelo nome correto do seu modelo)


#---------------------------- CRUD DE SALAS ----------------------------
@login_required
def buscar_salas(request):
    """
    View para buscar e filtrar salas.
    """
    # Contexto inicial
    context = {}

    # Verifica os grupos do usuário
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Adiciona informações de grupos ao contexto
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    # Filtra as salas com base nos grupos
    salas = filtrar_salas(request.user, is_coordenador, is_professor)

    # Aplica filtros de pesquisa e ordenação
    query = request.GET.get('q')
    ordem = request.GET.get('ordem')
    salas = aplicar_filtros_salas(salas, query, ordem)

    # Adiciona salas e formulário ao contexto
    context['sala'] = salas
    context['form'] = SalaForm()

    # Renderiza a página com o contexto
    return render(request, 'salas.html', context)

@login_required
def buscar_itens_sala(request):
    """
    View para buscar itens de inventário com base na sala e permissões do usuário.
    """
    # Contexto inicial
    context = {}

    # Obtém os parâmetros da requisição
    query = request.GET.get('q')  
    ordem = request.GET.get('ordem')  
    sala = request.GET.get('sala')  

    # Verifica grupos do usuário
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Filtra o inventário com base no grupo
    inventario = filtrar_inventario_por_grupo(request.user, is_coordenador, is_professor)

    # Aplica filtros adicionais
    inventario = aplicar_filtros_inventario(inventario, query, ordem, sala)

    # Adiciona informações ao contexto
    context['inventario'] = inventario
    context['form'] = InventarioForm()
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    # Renderiza a página
    return render(request, 'itens.html', context)



@login_required
def adicionar_salas(request):
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('welcomeHomepage')
    else:
        form = SalaForm()

    sala = Sala.objects.all()
    
    return render(request, 'welcomeHomepage.html', {'form': form, 'sala': sala})
@login_required
def update_sala(request):
    if request.method == 'POST':
        sala = request.POST.get('sala')
        
        # Busca a sala no banco de dados
        sala = get_object_or_404(Sala, sala=sala)

        # Atualiza os valores com base nos dados do formulário
        sala.descricao = request.POST.get('descricao')
        sala.localizacao = request.POST.get('localizacao')
        sala.link_imagem = request.POST.get('link_imagem')	
        sala.responsavel = request.POST.get('responsavel')
        sala.quantidade_itens = request.POST.get('quantidade_itens')
        sala.email_responsavel = request.POST.get('email_responsavel')
        sala.save()

        # Redireciona de volta à página de salas ou para onde você quiser
        return redirect('salas')  

    return HttpResponse("Método não permitido.", status=405)
@login_required
def excluir_sala(request):
    if request.method == 'POST':
        sala = request.POST.get('sala')
        
        # Exclui a sala com base no nome
        try:
            sala = Sala.objects.get(sala=sala)
            sala.delete()
            return redirect('salas')  # Redireciona para a lista de salas após exclusão
        except Sala.DoesNotExist:
            return HttpResponse("Sala não encontrada.", status=404)

@login_required
def salas(request):
    context = {}
    # Verifica os grupos do usuário
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Filtra as salas com base no grupo do usuário
    sala = filtrar_salas(request.user, is_coordenador, is_professor)

    # Gerenciamento de formulário (caso aplicável)
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('salas')
    else:
        form = SalaForm()

    form = SalaForm()
    context['form'] = form
    context['sala'] = sala
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    return render(request, 'salas.html', context)


#---------------------------- LOGIN E CADASTRO DE USUÁRIO ----------------------------
@login_required
def cadastroUsuario(request):
    context = {}
    dadosSenai = Senai.objects.all()
    context["dadosSenai"] = dadosSenai
    
    if request.method == 'POST':
        form = formCadastroUsuario(request.POST)
        if form.is_valid():
            var_nome = form.cleaned_data['first_name']
            var_sobrenome = form.cleaned_data['last_name']
            var_usuario = form.cleaned_data['user']
            var_email = form.cleaned_data['email']
            var_senha = form.cleaned_data['password']
            var_grupo = form.cleaned_data['group']  # Captura o grupo selecionado
            var_sala = form.cleaned_data['sala']  # Captura a sala selecionada
            # Cria o usuário
            user = User.objects.create_user(username=var_usuario, email=var_email, password=var_senha)
            user.first_name = var_nome
            user.last_name = var_sobrenome
            user.save()

            # Atribui o usuário ao grupo selecionado
            grupo = Group.objects.get(name=var_grupo)
            user.groups.add(grupo)
            

            return redirect('/welcomeHomepage')
            print('Cadastro realizado com sucesso')
    else:
        form = formCadastroUsuario()
        context['form'] = form
        print('Cadastro falhou')
    
    return render(request, 'cadastroUsuario.html', context)

def login(request):
    context = {}
    dadosSenai = Senai.objects.all()
    context["dadosSenai"] = dadosSenai
    if request.method == 'POST':
        form = FormLogin(request.POST)
        if form.is_valid():

            var_usuario = form.cleaned_data['user']
            var_senha = form.cleaned_data['password']
            
            user = authenticate(username=var_usuario, password=var_senha)

            if user is not None:
                auth_login(request, user)
                return redirect('/welcomeHomepage')  
            else:
                print('Login falhou')
    else:
        form = FormLogin()
        context['form'] = form
        return render(request, 'login.html', context)
    

#---------------------------- CRUD DE INVENTÁRIO ----------------------------
@login_required
def itens(request):
    context = {}
    # Verifica os grupos do usuário
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Filtra o inventário com base no grupo do usuário
    inventario = filtrar_inventario_por_grupo(request.user, is_coordenador, is_professor)

    # Gerenciamento de formulário (caso aplicável)
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('itens')  # Redireciona para a página de itens
    else:
        form = InventarioForm() 

    context['form'] = form
    context['inventario'] = inventario
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor
    form = InventarioForm()

    return render(request, 'itens.html', context)
    
    

@login_required
def adicionar_inventario(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirecionar para a rota inicial, independente de onde estava
    else:
        form = InventarioForm()
    
    # Se precisar listar todos os itens no modal de adição, inclua isso:
    inventario = Inventario.objects.all()
    
    return render(request, 'itens.html', {'form': form, 'inventario': inventario})

@login_required
def buscar_itens(request):
    context = {}
    query = request.GET.get('q')  # Pega o valor do campo de busca
    ordem = request.GET.get('ordem')  # Pega o valor da ordem A-Z ou Z-A
    sala = request.GET.get('sala')  # Pega o valor da sala
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)

    # Filtra o inventário com base no grupo do usuário
    inventario = filtrar_inventario_por_grupo(request.user, is_coordenador, is_professor)

    # Aplica filtros de pesquisa e ordenação
    inventario = aplicar_filtros_inventario(inventario, query, ordem, sala)

    context['inventario'] = inventario
    form = InventarioForm()
    context['form'] = form
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    return render(request, 'itens.html', context)


@login_required
def update_item(request):
    if request.method == 'POST':
        num_inventario = request.POST.get('numInventario')
        
        # Busca o item no banco de dados
        item = get_object_or_404(Inventario, num_inventario=num_inventario)

        # Atualiza os valores com base nos dados do formulário
        item.denominacao = request.POST.get('denominacao')
        item.localizacao = request.POST.get('localizacao')
        item.sala = request.POST.get('sala')
        item.link_imagem = request.POST.get('imagem')
        item.save()

        # Redireciona de volta à página de itens ou para onde você quiser
        return redirect('itens')  

    return HttpResponse("Método não permitido.", status=405)
@login_required
def excluir_inventario(request):
    if request.method == 'POST':
        num_inventario = request.POST.get('numInventario')
        
        # Exclui o item com base no número de inventário
        try:
            item = Inventario.objects.get(num_inventario=num_inventario)
            item.delete()
            return redirect('itens')  # Redireciona para a lista de itens após exclusão
        except Inventario.DoesNotExist:
            return HttpResponse("Item não encontrado.", status=404)
        




#---------------------------- PROFILE ----------------------------


@login_required
def profile(request):
    user = request.user
    sala = Sala.objects.filter(responsavel=user).first()  # Assume que 'responsavel' é o campo que liga o usuário à sala
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)
    if request.method == 'POST':
        # Atualiza os campos do usuário apenas se forem fornecidos novos valores
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Exibe uma mensagem de sucesso
        messages.success(request, "Perfil atualizado com sucesso.")
        return redirect('profile')  # Redireciona para evitar múltiplos envios do formulário

    context = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'id': user.id,
        'sala': sala.sala if sala else "Nenhuma sala atribuída",
        'is_coordenador': is_coordenador,
        'is_professor': is_professor,
    }

    return render(request, 'profile.html', context)





#---------------------------- Usuários ----------------------------#
@login_required
def gerenciar_usuarios(request):
    context = {}
    # Obtenha todos os usuários e informações dos grupos
    is_coordenador, is_professor = verificar_grupo_usuario(request.user)
    usuarios = User.objects.all().select_related()
    usuarios_info = []
    

    for user in usuarios:
        # Obtenha o grupo do usuário
        user_groups = user.groups.values_list('name', flat=True)
        role = "Professor" if "Professor" in user_groups else "Coordenador" if "Coordenador" in user_groups else ""

        # Adiciona o usuário e seu papel ao dicionário
        usuarios_info.append({
            'user': user,
            'role': role
        })

    # Processa o formulário de atualização de usuário
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            password = request.POST.get('password')
            
            # Atualiza a senha apenas se fornecida
            if password:
                user.set_password(password)
            
            user.save()
            return redirect('gerenciar_usuarios')
        except User.DoesNotExist:
            pass  # Gerencie erros se necessário
    
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor
    context['usuarios_info'] = usuarios_info
    return render(request, 'usuarios.html', context)


@login_required
def editar_usuario(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        return redirect('gerenciar_usuarios')
    
@login_required
def excluir_usuario(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        user.delete()
    return redirect('gerenciar_usuarios')