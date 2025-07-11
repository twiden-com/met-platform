from fastapi import APIRouter, Depends, status, HTTPException,Request
from fastapi.responses import HTMLResponse, JSONResponse
from src.config.database import get_admin_db, get_db
from src.config.templates import render
from supabase import Client, AsyncClient

router = APIRouter(prefix="/auth", tags=["Authentication"])

# =====================================================
# SIGNUP USER
# =====================================================
@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
     return await render("login.html", request)

@router.post("/signup")
async def signup_submit(
        request  : Request, 
        db       : AsyncClient = Depends(get_db), 
        admin_db : AsyncClient = Depends(get_admin_db)
    ):
    try:
        auth_result = await admin_db.auth.sign_up({
            "email"   : request.email,
            "password": request.password,
        })
        
        profile = await db.table("profiles").insert({
            "id"       : auth_result.user.id,
            "email"    : request.email,
            "full_name": request.full_name,
        }).execute()
        
        return {
            "user"    : auth_result.user,
            "profile" : profile.data[0],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# SIGNIN USER
# =====================================================
@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
     return await render("login.html", request)

@router.post("/login")
async def login_submit(request: Request, db = Depends(get_db)):
    try:
        result = await db.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        return {"user": result.user, "session": result.session}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))



async def send_otp(request: Request):

    

    return HTMLResponse("""
        <div class="form-container">
                <!-- Message Container -->
                <div class="message-container" id="message-container">
                    <div class="bx--inline-notification bx--inline-notification--success hidden" id="success-message">
                        <div class="bx--inline-notification__details">
                            <div class="bx--inline-notification__text-wrapper">
                                <p class="bx--inline-notification__subtitle" id="success-text"></p>
                            </div>
                        </div>
                    </div>

                    <div class="bx--inline-notification bx--inline-notification--error hidden" id="error-message">
                        <div class="bx--inline-notification__details">
                            <div class="bx--inline-notification__text-wrapper">
                                <p class="bx--inline-notification__subtitle" id="error-text"></p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sign In Form -->
                <div id="signin-form" class="form-transition form-visible">
                    <h1 class="form-title">Welcome back</h1>
                    <p class="form-subtitle">Sign in to your Medha Edu Tech account</p>

                    <form id="phone-form">
                        <!-- Phone Input Section -->
                        <div class="bx--form-item hidden" id="phone-section">
                            <label for="phone" class="bx--label">Phone number</label>
                            <div class="phone-input-wrapper">
                                <select id="country-code" class="country-dropdown">
                                    <option value="+91">🇮🇳 +91</option>
                                    <option value="+1">🇺🇸 +1</option>
                                    <option value="+44">🇬🇧 +44</option>
                                    <option value="+86">🇨🇳 +86</option>
                                    <option value="+49">🇩🇪 +49</option>
                                    <option value="+33">🇫🇷 +33</option>
                                    <option value="+81">🇯🇵 +81</option>
                                    <option value="+55">🇧🇷 +55</option>
                                    <option value="+61">🇦🇺 +61</option>
                                    <option value="+7">🇷🇺 +7</option>
                                </select>
                                <input type="tel" id="phone" class="bx--text-input phone-input" placeholder="Enter your phone number" required="" maxlength="15">
                            </div>
                        </div>

                        <!-- OTP Input Section -->
                        <div class="bx--form-item" id="otp-section">
                            <label class="bx--label">Enter OTP</label>
                            <div class="otp-container">
                                <div class="phone-display">
                                    <span class="phone-number" id="display-phone">+91 7013908751</span>
                                    <button type="button" class="edit-phone-btn" id="edit-phone">
                                        ✏️ Edit
                                    </button>
                                </div>
                                <div class="otp-inputs">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="0">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="1">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="2">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="3">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="4">
                                    <input type="text" class="otp-digit" maxlength="1" data-index="5">
                                </div>
                                <div class="resend-otp">
                                    <button type="button" id="resend-btn" disabled="">Resend OTP in <span id="countdown">24</span>s</button>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="bx--btn bx--btn--primary submit-btn" id="submit-btn">Verify &amp; Sign In</button>
                    </form>

                    <div class="forgot-password">
                        <a href="#" class="bx--link" id="forgot-link">
                            Don't have account?
                        </a>
                    </div>
                </div>

                <!-- Forgot Password Form -->
                <div id="forgot-form" class="form-transition form-hidden">
                    <h1 class="form-title">Reset Password</h1>
                    <p class="form-subtitle">Enter your phone number and we'll send you an OTP to reset your password</p>

                    <form id="forgot-phone-form">
                        <div class="bx--form-item">
                            <label for="forgot-phone" class="bx--label">Phone number</label>
                            <div class="phone-input-wrapper">
                                <select id="forgot-country-code" class="country-dropdown">
                                    <option value="+91">🇮🇳 +91</option>
                                    <option value="+1">🇺🇸 +1</option>
                                    <option value="+44">🇬🇧 +44</option>
                                    <option value="+86">🇨🇳 +86</option>
                                    <option value="+49">🇩🇪 +49</option>
                                    <option value="+33">🇫🇷 +33</option>
                                    <option value="+81">🇯🇵 +81</option>
                                    <option value="+55">🇧🇷 +55</option>
                                    <option value="+61">🇦🇺 +61</option>
                                    <option value="+7">🇷🇺 +7</option>
                                </select>
                                <input type="tel" id="forgot-phone" class="bx--text-input phone-input" placeholder="Enter your phone number" required="" maxlength="15">
                            </div>
                        </div>

                        <button type="submit" class="bx--btn bx--btn--primary submit-btn">Send Reset OTP</button>
                    </form>

                    <div class="back-to-login">
                        <a href="#" class="bx--link" id="back-to-signin">
                            ← Back to Sign In
                        </a>
                    </div>
                </div>
            </div>

        """)