import { render } from "@testing-library/react-native";

import { AudioEntryMode } from "@/components/add/AudioEntryMode";

jest.mock("@/hooks/useLanguage", () => ({
  useLanguage: () => ({
    t: (k: string) => k,
    language: "en",
    setLanguage: jest.fn(),
  }),
}));
jest.mock("@/components/voice/VoiceInputButton", () => ({
  VoiceInputButton: (props: any) => {
    const React = require("react");
    const { Text } = require("react-native");
    return React.createElement(
      Text,
      { testID: "voice-button" },
      "VoiceInputButton",
    );
  },
}));

describe("AudioEntryMode", () => {
  it("renders voice title", () => {
    const { getByText } = render(
      <AudioEntryMode onMealProcessed={jest.fn()} onError={jest.fn()} />,
    );
    expect(getByText("addFood.placeholders.voiceTitle")).toBeTruthy();
  });

  it("renders voice description", () => {
    const { getByText } = render(
      <AudioEntryMode onMealProcessed={jest.fn()} onError={jest.fn()} />,
    );
    expect(getByText("addFood.placeholders.voiceDesc")).toBeTruthy();
  });

  it("renders VoiceInputButton", () => {
    const { getByTestId } = render(
      <AudioEntryMode onMealProcessed={jest.fn()} onError={jest.fn()} />,
    );
    expect(getByTestId("voice-button")).toBeTruthy();
  });

  it("renders voice tip", () => {
    const { getByText } = render(
      <AudioEntryMode onMealProcessed={jest.fn()} onError={jest.fn()} />,
    );
    expect(getByText("addFood.voiceTip")).toBeTruthy();
  });
});
