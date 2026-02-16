from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Product, Cart, CartItem


# Home Page View
@require_http_methods(["GET"])
def home(request):
    products = Product.objects.all()[:6]
    context = {
        'products': products,
        'total_products': Product.objects.count()
    }
    return render(request, 'home.html', context)


# Products List View
@require_http_methods(["GET"])
def products_list(request):
    search = request.GET.get('search', '')
    if search:
        products = Product.objects.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    else:
        products = Product.objects.all()
    
    context = {
        'products': products,
        'search': search
    }
    return render(request, 'products.html', context)


# Product Detail View
@require_http_methods(["GET"])
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    context = {'product': product}
    return render(request, 'product_detail.html', context)


# Product Create View
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def product_create(request):
    if request.method == 'POST':
        if not request.user.is_staff:
            return redirect('home')
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        if name and price and stock:
            Product.objects.create(
                name=name,
                description=description,
                price=price,
                stock=stock
            )
            return redirect('products')
    
    return render(request, 'product_create.html')


# Product Update View
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.stock = request.POST.get('stock', product.stock)
        product.save()
        return redirect('product_detail', product_id=product.id)
    
    context = {'product': product}
    return render(request, 'product_update.html', context)


# Product Delete View
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        product.delete()
        return redirect('products')
    
    context = {'product': product}
    return render(request, 'product_delete.html', context)


# Register View
@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            context = {'error': 'Passwords do not match'}
            return render(request, 'register.html', context)
        
        if User.objects.filter(username=username).exists():
            context = {'error': 'Username already exists'}
            return render(request, 'register.html', context)
        
        if User.objects.filter(email=email).exists():
            context = {'error': 'Email already exists'}
            return render(request, 'register.html', context)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        Cart.objects.create(user=user)
        login(request, user)
        return redirect('home')
    
    return render(request, 'register.html')


# Login View
@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            context = {'error': 'Invalid credentials'}
            return render(request, 'login.html', context)
    
    return render(request, 'login.html')


# Logout View
@login_required(login_url='login')
@require_http_methods(["GET"])
def user_logout(request):
    logout(request)
    return redirect('home')


# Cart View
@login_required(login_url='login')
@require_http_methods(["GET"])
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        items = []
    
    total = sum(item.product.price * item.quantity for item in items)
    context = {
        'cart': cart,
        'items': items,
        'total': total
    }
    return render(request, 'cart.html', context)


# Add to Cart View
@login_required(login_url='login')
@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return redirect('view_cart')
