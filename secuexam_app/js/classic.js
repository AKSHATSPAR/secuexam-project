const CLASSIC_ROOT = "/classic";

function classicRolePath(role) {
    const roleMap = {
        setter: `${CLASSIC_ROOT}/setter`,
        receiver: `${CLASSIC_ROOT}/receiver`,
        admin: `${CLASSIC_ROOT}/admin`
    };
    return roleMap[role] || CLASSIC_ROOT;
}

function logout() {
    fetch("/api/logout", { method: "POST" })
        .catch(() => {})
        .finally(() => window.location.replace(CLASSIC_ROOT));
}

async function checkAuth(expectedRole) {
    try {
        const res = await fetch("/api/me");
        if (!res.ok) {
            window.location.href = CLASSIC_ROOT;
            return null;
        }
        const data = await res.json();
        if (expectedRole && data.role !== expectedRole) {
            window.location.href = classicRolePath(data.role);
            return null;
        }
        return data;
    } catch {
        window.location.href = CLASSIC_ROOT;
        return null;
    }
}
