package com.secuexam.mobile;

import android.app.KeyguardManager;
import android.content.pm.ApplicationInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.JSObject;
import java.util.concurrent.Executor;

public class MainActivity extends BridgeActivity {

    private static final long AUTO_RELOCK_MS = 45_000L;
    private static final String STATE_UNLOCKED = "secuexam_unlocked";
    private static final String STATE_LAST_UNLOCK = "secuexam_last_unlock";

    private FrameLayout securityOverlay;
    private TextView securitySubtitleView;
    private Button securityUnlockButton;
    private boolean securityAuthenticated = false;
    private boolean authPromptVisible = false;
    private boolean appLockSupported = false;
    private boolean biometricsAvailable = false;
    private boolean deviceCredentialAvailable = false;
    private long lastBackgroundElapsed = -1L;
    private long lastUnlockElapsed = -1L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(SecuExamSecurityPlugin.class);
        super.onCreate(savedInstanceState);
        refreshSecurityCapabilities();
        restoreSecurityState(savedInstanceState);
        configureWindowHardening();
        configureWebViewHardening();
        installSecurityOverlay();

        if (appLockSupported) {
            if (!securityAuthenticated) {
                promptForUnlock("Use fingerprint or device PIN to enter SecuExam.");
            } else {
                hideSecurityOverlay();
            }
        } else {
            securityAuthenticated = true;
            hideSecurityOverlay();
        }

        publishSecurityState();
    }

    @Override
    public void onResume() {
        super.onResume();
        configureWebViewHardening();
        if (!appLockSupported) {
            publishSecurityState();
            return;
        }

        if (shouldRequireUnlock()) {
            promptForUnlock("Secure session paused. Verify your identity to continue.");
        } else if (securityAuthenticated) {
            hideSecurityOverlay();
        }

        publishSecurityState();
    }

    @Override
    public void onStop() {
        if (appLockSupported && securityAuthenticated && !authPromptVisible) {
            lastBackgroundElapsed = SystemClock.elapsedRealtime();
        }
        super.onStop();
        publishSecurityState();
    }

    @Override
    public void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putBoolean(STATE_UNLOCKED, securityAuthenticated);
        outState.putLong(STATE_LAST_UNLOCK, lastUnlockElapsed);
    }

    public JSObject buildSecurityState() {
        JSObject data = new JSObject();
        data.put("nativeApp", true);
        data.put("appLockSupported", appLockSupported);
        data.put("appLockArmed", appLockSupported);
        data.put("biometricsAvailable", biometricsAvailable);
        data.put("deviceCredentialAvailable", deviceCredentialAvailable);
        data.put("secureWindowEnabled", true);
        data.put("screenCaptureBlocked", true);
        data.put("backupRestricted", true);
        data.put("autoRelockSeconds", AUTO_RELOCK_MS / 1000L);
        data.put("unlocked", securityAuthenticated);
        data.put("lockScreenVisible", securityOverlay != null && securityOverlay.getVisibility() == View.VISIBLE);
        data.put("secondsSinceUnlock", getSecondsSinceUnlock());
        data.put("nativeShellVersion", "2.0");
        return data;
    }

    public void lockNow() {
        if (!appLockSupported) {
            publishSecurityState();
            return;
        }
        securityAuthenticated = false;
        lastBackgroundElapsed = SystemClock.elapsedRealtime();
        promptForUnlock("Manual lock enabled. Re-authenticate to continue.");
    }

    private void restoreSecurityState(Bundle savedInstanceState) {
        if (savedInstanceState == null) {
            securityAuthenticated = !appLockSupported;
            return;
        }
        securityAuthenticated = savedInstanceState.getBoolean(STATE_UNLOCKED, !appLockSupported);
        lastUnlockElapsed = savedInstanceState.getLong(STATE_LAST_UNLOCK, -1L);
    }

    private void refreshSecurityCapabilities() {
        KeyguardManager keyguardManager = getSystemService(KeyguardManager.class);
        deviceCredentialAvailable = keyguardManager != null && keyguardManager.isDeviceSecure();

        BiometricManager biometricManager = BiometricManager.from(this);
        int biometricResult;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            biometricResult =
                biometricManager.canAuthenticate(
                    BiometricManager.Authenticators.BIOMETRIC_STRONG
                        | BiometricManager.Authenticators.DEVICE_CREDENTIAL
                );
        } else {
            biometricResult = biometricManager.canAuthenticate();
        }

        biometricsAvailable = biometricResult == BiometricManager.BIOMETRIC_SUCCESS;
        appLockSupported = deviceCredentialAvailable || biometricsAvailable;
    }

    private void configureWindowHardening() {
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE
        );
    }

    private void configureWebViewHardening() {
        boolean isDebuggable = (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        WebView.setWebContentsDebuggingEnabled(isDebuggable);
        if (getBridge() == null || getBridge().getWebView() == null) {
            return;
        }

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(getBridge().getWebView(), false);
        getBridge().getWebView().setOverScrollMode(View.OVER_SCROLL_NEVER);
    }

    private void installSecurityOverlay() {
        if (securityOverlay != null) {
            return;
        }

        FrameLayout root = findViewById(android.R.id.content);
        if (root == null) {
            return;
        }

        securityOverlay = new FrameLayout(this);
        securityOverlay.setLayoutParams(
            new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        );
        securityOverlay.setClickable(true);
        securityOverlay.setFocusable(true);
        securityOverlay.setPadding(dp(24), dp(24), dp(24), dp(24));
        securityOverlay.setBackground(buildOverlayBackground());

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER_HORIZONTAL);
        card.setPadding(dp(24), dp(28), dp(24), dp(24));
        card.setBackground(buildCardBackground());

        FrameLayout.LayoutParams cardParams = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        );
        cardParams.gravity = Gravity.CENTER;
        cardParams.leftMargin = dp(4);
        cardParams.rightMargin = dp(4);
        card.setLayoutParams(cardParams);

        TextView eyebrow = new TextView(this);
        eyebrow.setText("SECUEXAM MOBILE SHIELD");
        eyebrow.setTextColor(Color.parseColor("#7DD3FC"));
        eyebrow.setTextSize(12);
        eyebrow.setTypeface(Typeface.DEFAULT_BOLD);
        eyebrow.setLetterSpacing(0.08f);
        eyebrow.setGravity(Gravity.CENTER);

        TextView title = new TextView(this);
        title.setText("Secure console locked");
        title.setTextColor(Color.WHITE);
        title.setTextSize(24);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(14), 0, dp(8));

        securitySubtitleView = new TextView(this);
        securitySubtitleView.setTextColor(Color.parseColor("#B8CAE0"));
        securitySubtitleView.setTextSize(15);
        securitySubtitleView.setGravity(Gravity.CENTER);
        securitySubtitleView.setLineSpacing(0f, 1.18f);
        securitySubtitleView.setText("Authenticate with fingerprint or your device PIN to access SecuExam.");

        TextView featureStrip = new TextView(this);
        featureStrip.setText("App lock armed  •  Screen capture blocked  •  Auto relock after 45 sec");
        featureStrip.setTextColor(Color.parseColor("#8FA8C4"));
        featureStrip.setTextSize(13);
        featureStrip.setGravity(Gravity.CENTER);
        featureStrip.setPadding(0, dp(18), 0, dp(18));

        securityUnlockButton = new Button(this);
        securityUnlockButton.setAllCaps(false);
        securityUnlockButton.setText("Unlock Secure Console");
        securityUnlockButton.setTextColor(Color.parseColor("#02131D"));
        securityUnlockButton.setTypeface(Typeface.DEFAULT_BOLD);
        securityUnlockButton.setTextSize(16);
        securityUnlockButton.setPadding(dp(18), dp(12), dp(18), dp(12));
        securityUnlockButton.setBackground(buildPrimaryButtonBackground());
        securityUnlockButton.setOnClickListener(v ->
            promptForUnlock("Use fingerprint or device PIN to continue.")
        );

        card.addView(eyebrow);
        card.addView(title);
        card.addView(securitySubtitleView);
        card.addView(featureStrip);
        card.addView(securityUnlockButton);
        securityOverlay.addView(card);
        root.addView(securityOverlay);
    }

    private void promptForUnlock(String message) {
        if (!appLockSupported) {
            securityAuthenticated = true;
            hideSecurityOverlay();
            publishSecurityState();
            return;
        }
        if (authPromptVisible) {
            return;
        }

        showSecurityOverlay(message, true);
        authPromptVisible = true;
        securityUnlockButton.setEnabled(false);
        securityUnlockButton.setText("Waiting for authentication...");

        Executor executor = ContextCompat.getMainExecutor(this);
        BiometricPrompt biometricPrompt = new BiometricPrompt(
            this,
            executor,
            new BiometricPrompt.AuthenticationCallback() {
                @Override
                public void onAuthenticationSucceeded(@NonNull BiometricPrompt.AuthenticationResult result) {
                    authPromptVisible = false;
                    securityAuthenticated = true;
                    lastUnlockElapsed = SystemClock.elapsedRealtime();
                    lastBackgroundElapsed = -1L;
                    hideSecurityOverlay();
                    publishSecurityState();
                }

                @Override
                public void onAuthenticationFailed() {
                    super.onAuthenticationFailed();
                    showSecurityOverlay(
                        "Authentication not recognized yet. Try again or switch to your device credential.",
                        true
                    );
                    publishSecurityState();
                }

                @Override
                public void onAuthenticationError(int errorCode, @NonNull CharSequence errString) {
                    authPromptVisible = false;
                    securityAuthenticated = false;
                    showSecurityOverlay(
                        "Authentication canceled. Tap below and use fingerprint or your device PIN to continue.",
                        true
                    );
                    publishSecurityState();
                }
            }
        );

        BiometricPrompt.PromptInfo.Builder builder = new BiometricPrompt.PromptInfo.Builder()
            .setTitle("Unlock SecuExam")
            .setSubtitle("Biometric or device credential required")
            .setConfirmationRequired(false);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG
                    | BiometricManager.Authenticators.DEVICE_CREDENTIAL
            );
        } else {
            builder.setDeviceCredentialAllowed(true);
        }

        biometricPrompt.authenticate(builder.build());
    }

    private boolean shouldRequireUnlock() {
        if (!appLockSupported || authPromptVisible) {
            return false;
        }
        if (!securityAuthenticated) {
            return true;
        }
        if (lastBackgroundElapsed < 0L) {
            return false;
        }
        return SystemClock.elapsedRealtime() - lastBackgroundElapsed >= AUTO_RELOCK_MS;
    }

    private void showSecurityOverlay(String message, boolean enableButton) {
        if (securityOverlay == null) {
            return;
        }
        securityOverlay.setVisibility(View.VISIBLE);
        securitySubtitleView.setText(message);
        securityUnlockButton.setEnabled(enableButton);
        securityUnlockButton.setText(enableButton ? "Unlock Secure Console" : "Security control unavailable");

        if (getBridge() != null && getBridge().getWebView() != null) {
            getBridge().getWebView().setAlpha(0.08f);
        }
    }

    private void hideSecurityOverlay() {
        if (securityOverlay != null) {
            securityOverlay.setVisibility(View.GONE);
        }
        if (getBridge() != null && getBridge().getWebView() != null) {
            getBridge().getWebView().setAlpha(1f);
        }
    }

    private void publishSecurityState() {
        SecuExamSecurityPlugin plugin = SecuExamSecurityPlugin.getInstance();
        if (plugin != null) {
            plugin.broadcastSecurityState(buildSecurityState());
        }
    }

    private long getSecondsSinceUnlock() {
        if (lastUnlockElapsed < 0L) {
            return -1L;
        }
        return Math.max(0L, (SystemClock.elapsedRealtime() - lastUnlockElapsed) / 1000L);
    }

    private GradientDrawable buildOverlayBackground() {
        GradientDrawable background = new GradientDrawable(
            GradientDrawable.Orientation.TOP_BOTTOM,
            new int[] {
                Color.parseColor("#07111D"),
                Color.parseColor("#0D1F33")
            }
        );
        return background;
    }

    private GradientDrawable buildCardBackground() {
        GradientDrawable background = new GradientDrawable();
        background.setColor(Color.parseColor("#132236"));
        background.setCornerRadius(dp(24));
        background.setStroke(dp(1), Color.parseColor("#27405C"));
        return background;
    }

    private GradientDrawable buildPrimaryButtonBackground() {
        GradientDrawable background = new GradientDrawable(
            GradientDrawable.Orientation.LEFT_RIGHT,
            new int[] {
                Color.parseColor("#2DD4BF"),
                Color.parseColor("#38BDF8")
            }
        );
        background.setCornerRadius(dp(18));
        return background;
    }

    private int dp(int value) {
        return Math.round(getResources().getDisplayMetrics().density * value);
    }
}
