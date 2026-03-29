package com.secuexam.mobile;

import androidx.annotation.Nullable;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.lang.ref.WeakReference;

@CapacitorPlugin(name = "SecuExamSecurity")
public class SecuExamSecurityPlugin extends Plugin {

    private static WeakReference<SecuExamSecurityPlugin> instanceRef;

    @Override
    public void load() {
        instanceRef = new WeakReference<>(this);
    }

    @Nullable
    public static SecuExamSecurityPlugin getInstance() {
        return instanceRef == null ? null : instanceRef.get();
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        if (!(getActivity() instanceof MainActivity)) {
            call.reject("SecuExam security bridge is unavailable.");
            return;
        }
        call.resolve(((MainActivity) getActivity()).buildSecurityState());
    }

    @PluginMethod
    public void lockNow(PluginCall call) {
        if (!(getActivity() instanceof MainActivity)) {
            call.reject("SecuExam security bridge is unavailable.");
            return;
        }
        MainActivity activity = (MainActivity) getActivity();
        activity.runOnUiThread(() -> {
            activity.lockNow();
            call.resolve(activity.buildSecurityState());
        });
    }

    public void broadcastSecurityState(JSObject data) {
        notifyListeners("securityStatusChanged", data, true);
    }
}
