-- Migration: 00001_initial_schema.sql
-- Create custom types and enums
CREATE TYPE user_role_enum AS ENUM ('user', 'admin');
CREATE TYPE debt_type_enum AS ENUM ('receivable', 'payable');
CREATE TYPE debt_status_enum AS ENUM ('draft', 'active', 'partially_paid', 'paid', 'overdue', 'cancelled', 'disputed');
CREATE TYPE interest_type_enum AS ENUM ('none', 'percentage', 'fixed');
CREATE TYPE reminder_type_enum AS ENUM ('due_date', 'custom', 'overdue');
CREATE TYPE reminder_status_enum AS ENUM ('pending', 'sent', 'cancelled');
CREATE TYPE notification_type_enum AS ENUM ('info', 'warning', 'success', 'reminder', 'system');

-- 1. PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    avatar_url TEXT,
    role user_role_enum DEFAULT 'user' NOT NULL,
    timezone TEXT DEFAULT 'Asia/Jakarta',
    currency TEXT DEFAULT 'IDR',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. CONTACTS TABLE
CREATE TABLE IF NOT EXISTS public.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ
);

-- 3. DEBTS TABLE
CREATE TABLE IF NOT EXISTS public.debts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES public.contacts(id) ON DELETE CASCADE,
    type debt_type_enum NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    principal_amount NUMERIC(15, 2) NOT NULL CHECK (principal_amount > 0),
    paid_amount NUMERIC(15, 2) DEFAULT 0.00 NOT NULL CHECK (paid_amount >= 0),
    remaining_amount NUMERIC(15, 2) NOT NULL CHECK (remaining_amount >= 0),
    status debt_status_enum DEFAULT 'active' NOT NULL,
    transaction_date DATE DEFAULT CURRENT_DATE NOT NULL,
    due_date DATE,
    currency TEXT DEFAULT 'IDR' NOT NULL,
    interest_type interest_type_enum DEFAULT 'none' NOT NULL,
    interest_value NUMERIC(15, 2) DEFAULT 0.00 NOT NULL CHECK (interest_value >= 0),
    late_fee NUMERIC(15, 2) DEFAULT 0.00 NOT NULL CHECK (late_fee >= 0),
    reminder_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ
);

-- 4. DEBT_PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS public.debt_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debt_id UUID NOT NULL REFERENCES public.debts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    payment_date TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    payment_method TEXT DEFAULT 'cash',
    notes TEXT,
    evidence_url TEXT,
    idempotency_key TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ
);

-- 5. DEBT_EVIDENCES TABLE
CREATE TABLE IF NOT EXISTS public.debt_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debt_id UUID NOT NULL REFERENCES public.debts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 6. REMINDERS TABLE
CREATE TABLE IF NOT EXISTS public.reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debt_id UUID NOT NULL REFERENCES public.debts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reminder_date TIMESTAMPTZ NOT NULL,
    reminder_type reminder_type_enum DEFAULT 'due_date' NOT NULL,
    message TEXT NOT NULL,
    status reminder_status_enum DEFAULT 'pending' NOT NULL,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 7. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type notification_type_enum DEFAULT 'info' NOT NULL,
    reference_type TEXT,
    reference_id UUID,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    read_at TIMESTAMPTZ
);

-- 8. ACTIVITY_LOGS TABLE
CREATE TABLE IF NOT EXISTS public.activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON public.contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_debts_user_id ON public.debts(user_id);
CREATE INDEX IF NOT EXISTS idx_debts_contact_id ON public.debts(contact_id);
CREATE INDEX IF NOT EXISTS idx_debts_status ON public.debts(status);
CREATE INDEX IF NOT EXISTS idx_debts_due_date ON public.debts(due_date);
CREATE INDEX IF NOT EXISTS idx_debt_payments_debt_id ON public.debt_payments(debt_id);
CREATE INDEX IF NOT EXISTS idx_debt_payments_user_id ON public.debt_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_debt_evidences_debt_id ON public.debt_evidences(debt_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON public.reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON public.activity_logs(user_id);

-- TRIGGER FUNCTION FOR UPDATED_AT
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_contacts_updated_at BEFORE UPDATE ON public.contacts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_debts_updated_at BEFORE UPDATE ON public.debts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_debt_payments_updated_at BEFORE UPDATE ON public.debt_payments FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_reminders_updated_at BEFORE UPDATE ON public.reminders FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- AUTO CREATE PROFILE ON AUTH USER SIGNUP
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, avatar_url, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email,
        NEW.raw_user_meta_data->>'avatar_url',
        'user'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RECALCULATE DEBT TOTALS & STATUS TRIGGER
CREATE OR REPLACE FUNCTION public.recalculate_debt_totals()
RETURNS TRIGGER AS $$
DECLARE
    v_debt_id UUID;
    v_principal NUMERIC(15, 2);
    v_interest_type interest_type_enum;
    v_interest_val NUMERIC(15, 2);
    v_late_fee NUMERIC(15, 2);
    v_due_date DATE;
    v_curr_status debt_status_enum;
    v_total_paid NUMERIC(15, 2);
    v_total_interest NUMERIC(15, 2) := 0.00;
    v_total_due NUMERIC(15, 2);
    v_new_remaining NUMERIC(15, 2);
    v_new_status debt_status_enum;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        v_debt_id := OLD.debt_id;
    ELSE
        v_debt_id := NEW.debt_id;
    END IF;

    SELECT principal_amount, interest_type, interest_value, late_fee, due_date, status
    INTO v_principal, v_interest_type, v_interest_val, v_late_fee, v_due_date, v_curr_status
    FROM public.debts WHERE id = v_debt_id FOR UPDATE;

    IF v_principal IS NULL THEN
        RETURN NULL;
    END IF;

    IF v_interest_type = 'percentage' THEN
        v_total_interest := (v_principal * v_interest_val / 100.00);
    ELSIF v_interest_type = 'fixed' THEN
        v_total_interest := v_interest_val;
    END IF;

    v_total_due := v_principal + v_total_interest + v_late_fee;

    SELECT COALESCE(SUM(amount), 0.00) INTO v_total_paid
    FROM public.debt_payments
    WHERE debt_id = v_debt_id AND deleted_at IS NULL;

    v_new_remaining := v_total_due - v_total_paid;

    IF v_new_remaining < 0 THEN
        RAISE EXCEPTION 'Total pembayaran (%) melebihi total utang (%)', v_total_paid, v_total_due;
    END IF;

    IF v_new_remaining = 0 THEN
        v_new_status := 'paid';
    ELSIF v_total_paid > 0 THEN
        v_new_status := 'partially_paid';
    ELSIF v_due_date IS NOT NULL AND v_due_date < CURRENT_DATE AND v_curr_status != 'cancelled' AND v_curr_status != 'disputed' THEN
        v_new_status := 'overdue';
    ELSE
        v_new_status := 'active';
    END IF;

    UPDATE public.debts
    SET paid_amount = v_total_paid,
        remaining_amount = v_new_remaining,
        status = v_new_status,
        updated_at = NOW()
    WHERE id = v_debt_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_recalculate_debt ON public.debt_payments;
CREATE TRIGGER trg_recalculate_debt
    AFTER INSERT OR UPDATE OR DELETE ON public.debt_payments
    FOR EACH ROW EXECUTE FUNCTION public.recalculate_debt_totals();

-- RLS POLICIES
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.debts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.debt_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.debt_evidences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;

-- PROFILES Policies
CREATE POLICY "Users can view their own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- CONTACTS Policies
CREATE POLICY "Users can view their own contacts" ON public.contacts FOR SELECT USING (auth.uid() = user_id AND deleted_at IS NULL);
CREATE POLICY "Users can insert their own contacts" ON public.contacts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own contacts" ON public.contacts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own contacts" ON public.contacts FOR DELETE USING (auth.uid() = user_id);

-- DEBTS Policies
CREATE POLICY "Users can view their own debts" ON public.debts FOR SELECT USING (auth.uid() = user_id AND deleted_at IS NULL);
CREATE POLICY "Users can insert their own debts" ON public.debts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own debts" ON public.debts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own debts" ON public.debts FOR DELETE USING (auth.uid() = user_id);

-- DEBT PAYMENTS Policies
CREATE POLICY "Users can view their own debt payments" ON public.debt_payments FOR SELECT USING (auth.uid() = user_id AND deleted_at IS NULL);
CREATE POLICY "Users can insert their own debt payments" ON public.debt_payments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own debt payments" ON public.debt_payments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own debt payments" ON public.debt_payments FOR DELETE USING (auth.uid() = user_id);

-- DEBT EVIDENCES Policies
CREATE POLICY "Users can view their own evidences" ON public.debt_evidences FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own evidences" ON public.debt_evidences FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own evidences" ON public.debt_evidences FOR DELETE USING (auth.uid() = user_id);

-- REMINDERS Policies
CREATE POLICY "Users can view their own reminders" ON public.reminders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own reminders" ON public.reminders FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own reminders" ON public.reminders FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own reminders" ON public.reminders FOR DELETE USING (auth.uid() = user_id);

-- NOTIFICATIONS Policies
CREATE POLICY "Users can view their own notifications" ON public.notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update their own notifications" ON public.notifications FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own notifications" ON public.notifications FOR DELETE USING (auth.uid() = user_id);

-- ACTIVITY LOGS Policies
CREATE POLICY "Users can view their own activity logs" ON public.activity_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert activity logs" ON public.activity_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- STORAGE BUCKETS
INSERT INTO storage.buckets (id, name, public) VALUES ('avatars', 'avatars', true) ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public) VALUES ('evidences', 'evidences', false) ON CONFLICT (id) DO NOTHING;

-- STORAGE POLICIES
CREATE POLICY "Avatar public select" ON storage.objects FOR SELECT USING (bucket_id = 'avatars');
CREATE POLICY "Avatar user upload" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "Avatar user update" ON storage.objects FOR UPDATE USING (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "Avatar user delete" ON storage.objects FOR DELETE USING (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Evidence user select" ON storage.objects FOR SELECT USING (bucket_id = 'evidences' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "Evidence user upload" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'evidences' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "Evidence user delete" ON storage.objects FOR DELETE USING (bucket_id = 'evidences' AND auth.uid()::text = (storage.foldername(name))[1]);

-- REALTIME PUBLICATION
ALTER PUBLICATION supabase_realtime ADD TABLE public.debts;
ALTER PUBLICATION supabase_realtime ADD TABLE public.debt_payments;
ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
ALTER PUBLICATION supabase_realtime ADD TABLE public.reminders;
