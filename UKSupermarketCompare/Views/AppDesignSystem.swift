import SwiftUI

enum AppColors {
    static let brandBlue = Color(red: 0.10, green: 0.29, blue: 0.65)
    static let brandRed = Color(red: 0.85, green: 0.15, blue: 0.22)
    static let background = Color(red: 0.96, green: 0.97, blue: 0.99)
    static let card = Color.white
    static let textPrimary = Color(red: 0.13, green: 0.15, blue: 0.21)
    static let textSecondary = Color(red: 0.38, green: 0.41, blue: 0.49)
    static let divider = Color(red: 0.88, green: 0.90, blue: 0.94)
    static let success = Color(red: 0.12, green: 0.62, blue: 0.35)
}

enum AppSpacing {
    static let xs: CGFloat = 6
    static let sm: CGFloat = 10
    static let md: CGFloat = 16
    static let lg: CGFloat = 22
    static let xl: CGFloat = 30
}

enum AppTypography {
    static let hero = Font.system(size: 33, weight: .bold, design: .rounded)
    static let title = Font.system(size: 24, weight: .bold, design: .rounded)
    static let sectionTitle = Font.system(size: 18, weight: .semibold, design: .rounded)
    static let body = Font.system(size: 16, weight: .regular, design: .default)
    static let caption = Font.system(size: 13, weight: .medium, design: .default)
}

struct AppPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(.white)
            .padding(.vertical, AppSpacing.md)
            .frame(maxWidth: .infinity)
            .background(AppColors.brandRed.opacity(configuration.isPressed ? 0.86 : 1))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .shadow(color: AppColors.brandRed.opacity(0.2), radius: 8, y: 4)
    }
}

struct AppCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(AppSpacing.md)
            .background(AppColors.card)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(AppColors.divider, lineWidth: 1))
            .shadow(color: Color.black.opacity(0.04), radius: 8, y: 4)
    }
}

extension View {
    func appCardStyle() -> some View { modifier(AppCardModifier()) }
}

struct AppBadge: View {
    let text: String
    let tint: Color

    var body: some View {
        Text(text)
            .font(AppTypography.caption)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(tint.opacity(0.15))
            .foregroundStyle(tint)
            .clipShape(Capsule())
    }
}

struct AppSectionHeader: View {
    let title: String
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.xs) {
            Text(title)
                .font(AppTypography.sectionTitle)
                .foregroundStyle(AppColors.textPrimary)
            Text(subtitle)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
        }
    }
}

struct AppEmptyState: View {
    let icon: String
    let title: String
    let subtitle: String

    var body: some View {
        VStack(spacing: AppSpacing.sm) {
            Image(systemName: icon)
                .font(.system(size: 30))
                .foregroundStyle(AppColors.brandBlue)
            Text(title)
                .font(AppTypography.sectionTitle)
            Text(subtitle)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(AppSpacing.lg)
        .appCardStyle()
    }
}

struct AppLogoMark: View {
    var size: CGFloat = 56

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.25, style: .continuous)
                .fill(LinearGradient(colors: [AppColors.brandBlue, AppColors.brandRed], startPoint: .topLeading, endPoint: .bottomTrailing))
            Image(systemName: "basket.fill")
                .font(.system(size: size * 0.38, weight: .bold))
                .foregroundStyle(.white)
            Image(systemName: "sterlingsign.circle.fill")
                .font(.system(size: size * 0.24, weight: .bold))
                .foregroundStyle(.white.opacity(0.95))
                .offset(x: size * 0.24, y: -size * 0.24)
        }
        .frame(width: size, height: size)
    }
}

struct AppWordmark: View {
    var body: some View {
        HStack(spacing: 10) {
            AppLogoMark(size: 36)
            VStack(alignment: .leading, spacing: 0) {
                Text("UKSupermarket")
                    .font(.system(size: 17, weight: .bold, design: .rounded))
                    .foregroundStyle(AppColors.brandBlue)
                Text("Compare")
                    .font(.system(size: 17, weight: .heavy, design: .rounded))
                    .foregroundStyle(AppColors.brandRed)
            }
        }
    }
}
