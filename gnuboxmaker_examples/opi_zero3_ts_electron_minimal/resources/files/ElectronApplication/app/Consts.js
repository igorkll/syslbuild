import * as Three from 'three';

export const MAX_DELTA = 0.05;

export const SPHERE_DIAMETER = 1;
export const SPHERE_SEGMENTS = 64;

export const CAMERA_POS = new Three.Vector3(0, 3, 4);
export const CAMERA_LOOK = new Three.Vector3(0, 0, 0);

export const GRAVITY = 20;
export const JUMP_FORCE = 10;
export const GROUND_Y = 0;
export const GAMEOVER_Y = -8;
export const PLATFORM_DELETE_POSITION = 8;
export const BALL_DIAMETER_MUL_CHECK = 0.4;

export const HOR_VIEW_SIZE = 6;
export const LONG_PLATFORM_SIZE = 12;

export const CHANGE_BACKGROUND_AFTER_TIME = 60;
export const CHANGE_BACKGROUND_SMOOTHED_TIMER = 10;
export const CHANGE_BACKGROUND_SMOOTHED_SECONDS = 2;

export const RHYTHM_MIN = 0.2;
export const RHYTHM_MAX = 4;

export const DEFAULT_PLATFORM_WIDTH = 1.2;
export const DEFAULT_PLATFORM_HEIGHT = 0.2;
export const DEFAULT_PLATFORMS_COUNT = 20;
export const DEFAULT_PLATFORM_SPEED = 5;

export const DEFAULT_TRACK_RHYTHM = 1;
export const DEFAULT_TRACK_PLATFORM_WIDTH_MUL = 1;
export const DEFAULT_TRACK_BALL_DIAMETER_MUL = 1;
export const DEFAULT_TRACK_PLATFORM_SPEED_MUL = 1;

export const TRACK_SETS_MUL_MIN = 0.1;
export const TRACK_SETS_MUL_MAX = 2.5;

export const PLATFORM_SPEED_DEPENDENT_FROM_RHYTHM = 5;
export const PLATFORM_SPEED_MIN = 0.5;
export const MAX_RHYTHM_FOR_MATH_JUMP_FORCE = 1.1;

export const FOV = 75;

export const MAX_WIDTH = 600;
