from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Max
from django import forms
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from .models import User, Listing, Bid, Comment


def index(request):
    return render(request, "auctions/index.html", {"listings": Listing.objects.all()})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "auctions/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request, "auctions/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


Categorys = [
    ("optical-drive", "optical-drive"),
    ("case", "case"),
    ("cpu", "cpu"),
    ("motherboard", "motherboard"),
    ("speakers", "speakers"),
    ("cpu-cooler", "cpu-cooler"),
    ("video-card", "video-card"),
    ("memory", "memory"),
    ("fan-controller", "fan-controller"),
    ("wired-network-card", "wired-network-card"),
    ("mouse", "mouse"),
    ("internal-hard-drive", "internal-hard-drive"),
    ("sound-card", "sound-card"),
    ("monitor", "monitor"),
    ("ups", "ups"),
    ("keyboard", "keyboard"),
    ("case-fan", "case-fan"),
    ("wireless-network-card", "wireless-network-card"),
    ("external-hard-drive", "external-hard-drive"),
    ("thermal-paste", "thermal-paste"),
    ("headphones", "headphones"),
    ("power-supply", "power-supply"),
]


class NewListingForm(forms.Form):
    title = forms.CharField(label="Title:", required=True, max_length=64)
    description = forms.CharField(
        label="Item Description", widget=forms.Textarea, required=True, max_length=1000
    )
    starting = forms.IntegerField(
        label="Starting Bid ($)", min_value=0, max_value=999999, required=True
    )
    url = forms.CharField(label="Image URL", required=False, max_length=500)
    category = forms.CharField(
        label="Category",
        widget=forms.Select(choices=Categorys),
        required=True,
        max_length=64,
    )


class BidForm(forms.Form):
    amount = forms.IntegerField(
        label="Amount: ", min_value=0, max_value=999999, required=True
    )


class CommentForm(forms.Form):
    content = forms.CharField(
        label="Comment",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
        required=True,
        max_length=500,
    )


def new(request):
    if request.method == "POST":
        form = NewListingForm(request.POST)
        if form.is_valid():
            try:
                user = request.user
                title = form.cleaned_data["title"]
                description = form.cleaned_data["description"]
                starting = form.cleaned_data["starting"]
                url = form.cleaned_data["url"]
                category = form.cleaned_data["category"]

                listing = Listing(
                    user=user,
                    title=title,
                    description=description,
                    starting=starting,
                    url=url,
                    category=category,
                )
                listing.save()

                return render(
                    request,
                    "auctions/index.html",
                    {
                        "message": "Successfully added listing!.",
                        "listings": Listing.objects.all(),
                    },
                )
            except:
                return render(
                    request,
                    "auctions/new.html",
                    {
                        "message": "Error! The listing could not be created.",
                        "form": form,
                    },
                )
        else:
            return render(
                request,
                "auctions/new.html",
                {"message": "Error! Invalid form.", "form": form},
            )
    else:
        return render(request, "auctions/new.html", {"form": NewListingForm()})


def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    return render(
        request,
        "auctions/listing.html",
        {"listing": listing, "form": BidForm(), "commentForm": CommentForm()},
    )


def watchlist(request):
    return render(request, "auctions/watchlist.html", {})


def watchlist_update(request, update_type, item):
    if update_type == "add":
        request.user.watchlist.add(item)
    elif update_type == "remove":
        request.user.watchlist.remove(item)
    return HttpResponseRedirect(reverse("listing", args=(item,)))


def bid(request, listing_id):

    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            try:
                amount = int(form.cleaned_data["amount"])
                listing = Listing.objects.get(id=listing_id)
                max = listing.all_bids.aggregate(Max("amount"))["amount__max"]
                if not max: 
                    max = listing.starting -1
                
                if amount <= max :

                    messages.warning(
                        request,
                        ("New bids must be greater than the highest current bid!"),
                    )
                    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

                user = request.user

                bid = Bid(user=user, listing=listing, amount=amount)
                bid.save()
            except:
                messages.info(request, ("The bid could not be placed!"))
                return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

    messages.success(request, ("Bid placed successfully!"))
    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))


def close(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    listing.active = False

    listing.save()

    return HttpResponseRedirect(reverse("index"))


def comment(request, listing_id):

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # try:
            content = form.cleaned_data["content"]
            listing = Listing.objects.get(id=listing_id)
            user = request.user
            comment = Comment(user=user, listing=listing, content=content)
            comment.save()
        # except:
        #     messages.error(request, ('Comment could not be made!'))
        #     return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

    messages.success(request, ("Comment made successfully!"))
    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))


def categories(request):
    cats = ("optical-drive",
    "case",
    "cpu",
    "motherboard",
    "speakers",
    "cpu-cooler",
    "video-card",
    "memory",
    "fan-controller",
    "wired-network-card",
    "mouse",
    "internal-hard-drive",
    "sound-card",
    "monitor",
    "ups",
    "keyboard",
    "case-fan",
    "wireless-network-card",
    "external-hard-drive",
    "thermal-paste",
    "headphones",
    "power-supply")

    return render(request, "auctions/categories.html", {"categories": cats})


def category(request, category):
    

    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(category=category),
        "category": category})


def search(request):

    if request.method == "GET":

        # Attempt to sign user in
        search_query = request.GET["search"]
 

        return render(request, "auctions/index.html", {
            "listings": Listing.objects.filter( title__contains=search_query),
            "search":  "results"})
