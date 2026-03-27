"""
Users app modellari - User va SellerProfile
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager - telegram_id orqali user yaratish"""

    def create_user(self, telegram_id, username, first_name, **extra_fields):
        if not telegram_id:
            raise ValueError('Telegram ID kiritilishi shart')
        user = self.model(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            **extra_fields
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, username, first_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(telegram_id, username, first_name, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Foydalanuvchi modeli.
    Telegram orqali autentifikatsiya qilinadi.
    """

    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Xaridor'
        SELLER = 'seller', 'Sotuvchi'

    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=150, unique=True, verbose_name='Username')
    first_name = models.CharField(max_length=150, verbose_name='Ism')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='Familiya')
    phone_number = models.CharField(max_length=20, blank=True, verbose_name='Telefon raqami')
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Rol'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Profil rasmi')
    is_active = models.BooleanField(default=True, verbose_name='Faolmi')
    is_staff = models.BooleanField(default=False, verbose_name='Admin')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Ro\'yxatdan o\'tgan sana')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Oxirgi kirish')

    objects = UserManager()

    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = ['username', 'first_name']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} (@{self.username})"

    @property
    def full_name(self):
        """To'liq ism"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_seller(self):
        """Sotuvchimi?"""
        return self.role == self.Role.SELLER


class SellerProfile(models.Model):
    """
    Sotuvchi profili - User bilan OneToOne bog'lanish.
    Faqat seller rolidagi userlar uchun.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        verbose_name='Foydalanuvchi'
    )
    shop_name = models.CharField(max_length=200, unique=True, verbose_name='Do\'kon nomi')
    shop_description = models.TextField(blank=True, verbose_name='Do\'kon tavsifi')
    shop_logo = models.ImageField(
        upload_to='shop_logos/',
        blank=True,
        null=True,
        verbose_name='Do\'kon logosi'
    )
    region = models.CharField(max_length=100, verbose_name='Viloyat')
    district = models.CharField(max_length=100, verbose_name='Tuman')
    address = models.CharField(max_length=300, blank=True, verbose_name='Manzil')
    rating = models.FloatField(default=0.0, verbose_name='Reyting')
    total_sales = models.PositiveIntegerField(default=0, verbose_name='Sotuvlar soni')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')

    class Meta:
        verbose_name = 'Sotuvchi profili'
        verbose_name_plural = 'Sotuvchi profillari'
        ordering = ['-rating']

    def __str__(self):
        return f"{self.shop_name} ({self.user.full_name})"

    def update_rating(self):
        """Barcha reviewlar asosida reytingni yangilash"""
        from apps.reviews.models import Review
        reviews = Review.objects.filter(seller=self.user)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 2)
        else:
            self.rating = 0.0
        self.save(update_fields=['rating'])