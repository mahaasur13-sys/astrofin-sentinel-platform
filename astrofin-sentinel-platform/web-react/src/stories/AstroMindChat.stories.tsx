import type { Meta, StoryObj } from '@storybook/react';
import AstroMindChat from '../components/astro/AstroMindChat';

const meta: Meta<typeof AstroMindChat> = {
  title: 'Widgets/AstroMindChat',
  component: AstroMindChat,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['embedded', 'floating'] },
    className: { control: 'text' },
  },
  decorators: [
    (Story) => (
      <div className="rounded-xl border border-gray-800 bg-gray-950">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof AstroMindChat>;

export const Embedded: Story = {
  args: { variant: 'embedded' },
  name: 'Embedded (sidebar)',
};

export const Floating: Story = {
  args: { variant: 'floating', className: 'max-w-md' },
  name: 'Floating (popup)',
};
