<script lang="ts">
  import { goto } from '$app/navigation';
  import { Button } from "$lib/components/ui/button";
  import { Calendar, Clock, Users, Shield, CheckCircle, ArrowRight } from "lucide-svelte";
  import { user } from '$lib/stores/user';
  
  // Redirect if already logged in
  $effect(() => {
    if ($user) {
      if ($user.role === 'admin') {
        goto('/dashboard');
      } else {
        goto('/reservations');
      }
    }
  });
</script>

<svelte:head>
  <title>B-Hive - Hall Reservation System</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-purple-50 via-violet-50 to-fuchsia-50">
  <nav class="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
    <div class="container mx-auto px-4 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img src="/src/lib/assets/bhive.png" alt="B-Hive Logo" class="h-10 w-16" />
        <div>
          <h1 class="text-xl font-semibold text-gray-800">B-Hive</h1>
          <p class="text-xs text-gray-500">Buri's Great Hall</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" onclick={() => goto('/login-01')} class="border-[#6B2AB9] text-[#6B2AB9] hover:bg-purple-50">
          Login
        </Button>
        <Button onclick={() => goto('/register')} class="bg-[#6B2AB9] hover:bg-[#5a229a] text-white">
          Get Started
        </Button>
      </div>
    </div>
  </nav>

  <section class="container mx-auto px-4 py-20 md:py-32">
    <div class="grid md:grid-cols-2 gap-12 items-center">
      <div class="space-y-6">
        <div class="inline-block px-4 py-2 bg-purple-100 text-[#6B2AB9] rounded-full text-sm font-medium">
          Simplify Your Hall Bookings
        </div>
        <h1 class="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
          Reserve Your Space in
          <span class="text-[#6B2AB9] block">Seconds</span>
        </h1>
        <p class="text-xl text-gray-600 leading-relaxed">
          The modern reservation system for Buri, Raya, and Adarna halls. Book spaces effortlessly, 
          manage approvals seamlessly, and make the most of your time.
        </p>
        <div class="flex flex-wrap gap-4">
          <Button size="lg" onclick={() => goto('/register')} class="bg-[#6B2AB9] hover:bg-[#5a229a] text-white text-lg px-8">
            Start Booking Now
            <ArrowRight class="ml-2 h-5 w-5" />
          </Button>
          <Button size="lg" variant="outline" onclick={() => goto('/login-01')} class="text-lg px-8 border-2 border-[#6B2AB9] text-[#6B2AB9] hover:bg-purple-50">
            Sign In
          </Button>
        </div>
        <div class="flex items-center gap-8 pt-4">
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900">500+</div>
            <div class="text-sm text-gray-600">Reservations</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900">3</div>
            <div class="text-sm text-gray-600">Halls</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900">100%</div>
            <div class="text-sm text-gray-600">Satisfaction</div>
          </div>
        </div>
      </div>
      <div class="relative">
        <div class="relative rounded-2xl overflow-hidden shadow-2xl border-8 border-white">
          <img 
            src="https://images.unsplash.com/photo-1505373877841-8d25f7d46678?w=800&h=600&fit=crop" 
            alt="Modern Event Hall" 
            class="w-full h-auto"
          />
        </div>
        <div class="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-lg p-4 border">
          <div class="flex items-center gap-3">
            <div class="bg-green-100 p-3 rounded-lg">
              <CheckCircle class="h-6 w-6 text-green-600" />
            </div>
            <div>
              <div class="font-semibold text-gray-900">Instant Confirmation</div>
              <div class="text-sm text-gray-600">Book in real-time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="bg-white py-20">
    <div class="container mx-auto px-4">
      <div class="text-center mb-16">
        <h2 class="text-4xl font-bold text-gray-900 mb-4">Everything You Need</h2>
        <p class="text-xl text-gray-600">Powerful features to make hall booking a breeze</p>
      </div>
      
      <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        <div class="text-center p-6 rounded-xl hover:bg-gray-50 transition-colors">
          <div class="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Calendar class="h-8 w-8 text-[#6B2AB9]" />
          </div>
          <h3 class="text-xl font-semibold mb-2">Easy Scheduling</h3>
          <p class="text-gray-600">View availability and book your preferred time slots instantly</p>
        </div>
        
        <div class="text-center p-6 rounded-xl hover:bg-gray-50 transition-colors">
          <div class="bg-violet-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Clock class="h-8 w-8 text-violet-600" />
          </div>
          <h3 class="text-xl font-semibold mb-2">Primetime Booking</h3>
          <p class="text-gray-600">Special time slots with admin approval for peak hours</p>
        </div>
        
        <div class="text-center p-6 rounded-xl hover:bg-gray-50 transition-colors">
          <div class="bg-fuchsia-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users class="h-8 w-8 text-fuchsia-600" />
          </div>
          <h3 class="text-xl font-semibold mb-2">Manage Bookings</h3>
          <p class="text-gray-600">Track all your reservations in one convenient dashboard</p>
        </div>
        
        <div class="text-center p-6 rounded-xl hover:bg-gray-50 transition-colors">
          <div class="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield class="h-8 w-8 text-purple-700" />
          </div>
          <h3 class="text-xl font-semibold mb-2">Secure & Reliable</h3>
          <p class="text-gray-600">Your data is protected with enterprise-grade security</p>
        </div>
      </div>
    </div>
  </section>

  <!-- How It Works Section -->
  <section class="py-20 bg-gradient-to-br from-purple-50 to-violet-100">
    <div class="container mx-auto px-4">
      <div class="text-center mb-16">
        <h2 class="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
        <p class="text-xl text-gray-600">Three simple steps to secure your hall</p>
      </div>
      
      <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <div>
          <div class="bg-white rounded-xl p-8 shadow-lg border-2 border-purple-100 hover:border-purple-300 transition-colors flex flex-col h-full">
            <div class="flex items-start gap-4">
              <div class="bg-[#6B2AB9] text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg flex-shrink-0">1</div>
              <div class="flex-1">
                <h3 class="text-2xl font-semibold mb-3 mt-0 text-gray-900">Sign Up</h3>
                <p class="text-gray-600">Create your free account in less than a minute. No credit card required.</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div class="bg-white rounded-xl p-8 shadow-lg border-2 border-purple-100 hover:border-purple-300 transition-colors flex flex-col h-full">
            <div class="flex items-start gap-4">
              <div class="bg-[#6B2AB9] text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg flex-shrink-0">2</div>
              <div class="flex-1">
                <h3 class="text-2xl font-semibold mb-3 mt-0 text-gray-900">Choose Date & Time</h3>
                <p class="text-gray-600">Browse available slots and select the perfect time for your event.</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div class="bg-white rounded-xl p-8 shadow-lg border-2 border-purple-100 hover:border-purple-300 transition-colors flex flex-col h-full">
            <div class="flex items-start gap-4">
              <div class="bg-[#6B2AB9] text-white w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl shadow-lg flex-shrink-0">3</div>
              <div class="flex-1">
                <h3 class="text-2xl font-semibold mb-3 mt-0 text-gray-900">Get Confirmed</h3>
                <p class="text-gray-600">Receive instant confirmation or await approval for primetime slots.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="bg-gradient-to-r from-[#6B2AB9] to-purple-600 py-20">
    <div class="container mx-auto px-4 text-center">
      <h2 class="text-4xl md:text-5xl font-bold text-white mb-6">
        Ready to Get Started?
      </h2>
      <p class="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
        Join hundreds of users who trust B-Hive for their hall reservations. 
        Start booking today and experience seamless event management.
      </p>
      <div class="flex flex-wrap gap-4 justify-center">
        <Button 
          size="lg" 
          onclick={() => goto('/register')} 
          class="bg-white text-[#6B2AB9] hover:bg-gray-100 text-lg px-8"
        >
          Create Free Account
          <ArrowRight class="ml-2 h-5 w-5" />
        </Button>
        <Button 
          size="lg" 
          variant="outline" 
          onclick={() => goto('/login-01')} 
          class="bg-white text-[#6B2AB9] hover:bg-gray-100 text-lg px-8"
        >
          Sign In
        </Button>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-gray-900 text-white py-12">
    <div class="container mx-auto px-4">
      <div class="grid md:grid-cols-3 gap-8">
        <div>
          <div class="flex items-center gap-2 mb-4">
            <img src="/src/lib/assets/bhive.png" alt="B-Hive Logo" class="h-8 w-12" />
            <h3 class="text-xl font-semibold">B-Hive</h3>
          </div>
          <p class="text-gray-400">
            From Buri to Raya to Adarna, one hall for all.
          </p>
        </div>
        <div>
          <h4 class="font-semibold mb-4">Quick Links</h4>
          <ul class="space-y-2 text-gray-400">
            <li><a href="/login-01" class="hover:text-white transition-colors">Login</a></li>
            <li><a href="/register" class="hover:text-white transition-colors">Register</a></li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-4">Contact</h4>
          <p class="text-gray-400">
            Mars, Jupiter<br />
            Cavite, Philippines
          </p>
        </div>
      </div>
      <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
        <p>&copy; 2025 B-Hive. All rights reserved.</p>
      </div>
    </div>
  </footer>
</div>
