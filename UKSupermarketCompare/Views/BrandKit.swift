import SwiftUI
import UIKit

enum BrandPalette {
    static let red = Color(red: 0.84, green: 0.14, blue: 0.23)
    static let blue = Color(red: 0.08, green: 0.33, blue: 0.77)
    static let navy = Color(red: 0.05, green: 0.13, blue: 0.31)
    static let sky = Color(red: 0.87, green: 0.93, blue: 1.0)
    static let cloud = Color(red: 0.96, green: 0.98, blue: 1.0)
    static let textPrimary = Color(red: 0.12, green: 0.16, blue: 0.25)
    static let textSecondary = Color(red: 0.34, green: 0.41, blue: 0.53)
    static let success = Color(red: 0.10, green: 0.58, blue: 0.33)
    static let warning = Color(red: 0.93, green: 0.57, blue: 0.12)
}

enum BrandTypography {
    static let hero = Font.system(size: 34, weight: .bold, design: .rounded)
    static let title = Font.system(.title3, design: .rounded).weight(.semibold)
    static let section = Font.system(.headline, design: .rounded).weight(.semibold)
    static let body = Font.system(.body, design: .rounded)
    static let caption = Font.system(.caption, design: .rounded)
}

struct BrandLogoMark: View {
    var size: CGFloat = 52

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.27, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [BrandPalette.blue, BrandPalette.red],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            Circle()
                .stroke(.white.opacity(0.25), lineWidth: size * 0.06)
                .padding(size * 0.12)

            Image(systemName: "basket.fill")
                .font(.system(size: size * 0.37, weight: .bold))
                .foregroundStyle(.white)

            Image(systemName: "sterlingsign")
                .font(.system(size: size * 0.24, weight: .heavy))
                .foregroundStyle(.white)
                .offset(x: size * 0.22, y: -size * 0.22)
        }
        .frame(width: size, height: size)
        .shadow(color: BrandPalette.blue.opacity(0.22), radius: 8, y: 5)
    }
}

struct BrandLogoView: View {
    var title: String = "UKSupermarketCompare"
    var subtitle: String = "Smart grocery savings"

    var body: some View {
        HStack(spacing: 12) {
            BrandLogoMark()

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(BrandTypography.title)
                    .foregroundStyle(BrandPalette.navy)
                Text(subtitle)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
    }
}

struct BrandHeader: View {
    let title: String
    let subtitle: String

    var body: some View {
        BrandCard {
            HStack(alignment: .top, spacing: 12) {
                BrandLogoMark(size: 44)
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(BrandTypography.section)
                        .foregroundStyle(BrandPalette.navy)
                    Text(subtitle)
                        .font(BrandTypography.caption)
                        .foregroundStyle(BrandPalette.textSecondary)
                }
                Spacer()
                BrandBadge(text: "UK", tint: BrandPalette.red)
            }
        }
    }
}

struct BrandPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(BrandTypography.section)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [BrandPalette.red, BrandPalette.blue],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
            )
            .opacity(configuration.isPressed ? 0.9 : 1)
            .scaleEffect(configuration.isPressed ? 0.99 : 1)
    }
}

struct BrandSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(BrandTypography.section)
            .foregroundStyle(BrandPalette.blue)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(.white)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(BrandPalette.blue.opacity(0.35), lineWidth: 1.5)
            )
            .opacity(configuration.isPressed ? 0.9 : 1)
    }
}

struct BrandGhostButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(BrandTypography.caption.weight(.semibold))
            .foregroundStyle(BrandPalette.blue)
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(BrandPalette.blue.opacity(0.1))
            .clipShape(Capsule())
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

struct BrandCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(.white)
                    .shadow(color: BrandPalette.blue.opacity(0.10), radius: 12, x: 0, y: 6)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(BrandPalette.blue.opacity(0.08), lineWidth: 1)
            )
    }
}

struct BrandBadge: View {
    let text: String
    var tint: Color = BrandPalette.blue

    var body: some View {
        Text(text)
            .font(BrandTypography.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .foregroundStyle(tint)
            .background(tint.opacity(0.12))
            .clipShape(Capsule())
    }
}

struct BrandChip: View {
    let text: String
    var tint: Color = BrandPalette.navy

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(tint)
                .frame(width: 6, height: 6)
            Text(text)
                .font(BrandTypography.caption)
        }
        .foregroundStyle(tint)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(tint.opacity(0.11))
        .clipShape(Capsule())
    }
}

struct BrandScreenBackground: ViewModifier {
    func body(content: Content) -> some View {
        content
            .scrollContentBackground(.hidden)
            .background(
                LinearGradient(
                    colors: [BrandPalette.cloud, BrandPalette.sky.opacity(0.78), BrandPalette.cloud],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
            )
    }
}

extension View {
    func brandScreenBackground() -> some View {
        modifier(BrandScreenBackground())
    }
}


private struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = -0.7

    func body(content: Content) -> some View {
        content
            .overlay(
                GeometryReader { proxy in
                    LinearGradient(
                        colors: [.clear, .white.opacity(0.45), .clear],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                    .frame(width: proxy.size.width * 0.7)
                    .offset(x: proxy.size.width * phase)
                }
                .mask(content)
            )
            .onAppear {
                withAnimation(.linear(duration: 1.0).repeatForever(autoreverses: false)) {
                    phase = 1.1
                }
            }
    }
}

extension View {
    func shimmering() -> some View {
        modifier(ShimmerModifier())
    }
}


enum HapticFeedbackService {
    static func addItem() {
        impact(.light)
    }

    static func compareBasket() {
        impact(.medium)
    }

    static func saveBasket() {
        notify(.success)
    }

    static func bestOptionSelected() {
        impact(.rigid)
    }

    private static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.prepare()
        generator.impactOccurred()
    }

    private static func notify(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(type)
    }
}
