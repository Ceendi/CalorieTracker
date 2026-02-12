import {
  createLoginSchema,
  createRegisterSchema,
  createVerificationSchema,
  createForgotPasswordSchema,
  createChangePasswordSchema,
  createResetPasswordSchema,
} from '../../../utils/validators';

const t = (key: string) => key;

describe('createLoginSchema', () => {
  const schema = createLoginSchema(t);

  it('accepts valid data', () => {
    const result = schema.safeParse({ username: 'user@example.com', password: 'pass123' });
    expect(result.success).toBe(true);
  });

  it('rejects empty email', () => {
    const result = schema.safeParse({ username: '', password: 'pass123' });
    expect(result.success).toBe(false);
  });

  it('rejects invalid email', () => {
    const result = schema.safeParse({ username: 'notanemail', password: 'pass123' });
    expect(result.success).toBe(false);
  });

  it('rejects empty password', () => {
    const result = schema.safeParse({ username: 'user@example.com', password: '' });
    expect(result.success).toBe(false);
  });
});

describe('createRegisterSchema', () => {
  const schema = createRegisterSchema(t);

  it('accepts valid registration data', () => {
    const result = schema.safeParse({
      email: 'user@example.com',
      password: 'Password1',
      confirmPassword: 'Password1',
    });
    expect(result.success).toBe(true);
  });

  it('rejects password shorter than 8 chars', () => {
    const result = schema.safeParse({
      email: 'user@example.com',
      password: 'Pass1',
      confirmPassword: 'Pass1',
    });
    expect(result.success).toBe(false);
  });

  it('rejects password without uppercase', () => {
    const result = schema.safeParse({
      email: 'user@example.com',
      password: 'password1',
      confirmPassword: 'password1',
    });
    expect(result.success).toBe(false);
  });

  it('rejects password without number', () => {
    const result = schema.safeParse({
      email: 'user@example.com',
      password: 'Password',
      confirmPassword: 'Password',
    });
    expect(result.success).toBe(false);
  });

  it('rejects non-matching passwords', () => {
    const result = schema.safeParse({
      email: 'user@example.com',
      password: 'Password1',
      confirmPassword: 'Password2',
    });
    expect(result.success).toBe(false);
  });

  it('rejects empty email', () => {
    const result = schema.safeParse({
      email: '',
      password: 'Password1',
      confirmPassword: 'Password1',
    });
    expect(result.success).toBe(false);
  });
});

describe('createVerificationSchema', () => {
  const schema = createVerificationSchema(t);

  it('accepts 6-character code', () => {
    const result = schema.safeParse({ code: '123456' });
    expect(result.success).toBe(true);
  });

  it('rejects too short code', () => {
    const result = schema.safeParse({ code: '12345' });
    expect(result.success).toBe(false);
  });

  it('rejects too long code', () => {
    const result = schema.safeParse({ code: '1234567' });
    expect(result.success).toBe(false);
  });

  it('rejects empty code', () => {
    const result = schema.safeParse({ code: '' });
    expect(result.success).toBe(false);
  });
});

describe('createForgotPasswordSchema', () => {
  const schema = createForgotPasswordSchema(t);

  it('accepts valid email', () => {
    const result = schema.safeParse({ email: 'user@example.com' });
    expect(result.success).toBe(true);
  });

  it('rejects empty email', () => {
    const result = schema.safeParse({ email: '' });
    expect(result.success).toBe(false);
  });

  it('rejects invalid email', () => {
    const result = schema.safeParse({ email: 'notanemail' });
    expect(result.success).toBe(false);
  });
});

describe('createChangePasswordSchema', () => {
  const schema = createChangePasswordSchema(t);

  it('accepts valid change password data', () => {
    const result = schema.safeParse({
      oldPassword: 'OldPass1',
      newPassword: 'NewPass1',
      confirmPassword: 'NewPass1',
    });
    expect(result.success).toBe(true);
  });

  it('rejects empty old password', () => {
    const result = schema.safeParse({
      oldPassword: '',
      newPassword: 'NewPass1',
      confirmPassword: 'NewPass1',
    });
    expect(result.success).toBe(false);
  });

  it('rejects new password shorter than 8', () => {
    const result = schema.safeParse({
      oldPassword: 'OldPass1',
      newPassword: 'New1',
      confirmPassword: 'New1',
    });
    expect(result.success).toBe(false);
  });

  it('rejects new password without uppercase', () => {
    const result = schema.safeParse({
      oldPassword: 'OldPass1',
      newPassword: 'newpass12',
      confirmPassword: 'newpass12',
    });
    expect(result.success).toBe(false);
  });

  it('rejects non-matching passwords', () => {
    const result = schema.safeParse({
      oldPassword: 'OldPass1',
      newPassword: 'NewPass1',
      confirmPassword: 'NewPass2',
    });
    expect(result.success).toBe(false);
  });
});

describe('createResetPasswordSchema', () => {
  const schema = createResetPasswordSchema(t);

  it('accepts valid reset data', () => {
    const result = schema.safeParse({ password: 'NewPass1', confirmPassword: 'NewPass1' });
    expect(result.success).toBe(true);
  });

  it('rejects too short password', () => {
    const result = schema.safeParse({ password: 'New1', confirmPassword: 'New1' });
    expect(result.success).toBe(false);
  });

  it('rejects password without number', () => {
    const result = schema.safeParse({ password: 'NewPasss', confirmPassword: 'NewPasss' });
    expect(result.success).toBe(false);
  });

  it('rejects non-matching passwords', () => {
    const result = schema.safeParse({ password: 'NewPass1', confirmPassword: 'NewPass2' });
    expect(result.success).toBe(false);
  });
});
